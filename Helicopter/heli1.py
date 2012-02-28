import pygame, sys
from pygame.locals import*
import random
from datetime import datetime
import time
import continuousMuscleTesting

def quit():
	controls.quit()
	pygame.quit()
	sys.exit()

def displayString(s):
	windowSurfaceObj.fill(backgroundColor)
	surface = fontObj.render(s, False, scoreColor)
	disp_rect = surface.get_rect()
	disp_rect.center = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
	windowSurfaceObj.blit(surface, disp_rect)
	pygame.display.update()
	
class ControlType():
	KEYBOARD = 1
	MUSCLE_ANALOG = 2
	MUSCLE_DIGITAL = 3
	
class KeyboardControls():
	def __init__(self):
		self.isDown = 0
		pass
	def getUpAccel(self, events = []):
		for event in events:
			if event.type == KEYDOWN and event.key == K_SPACE:
				self.isDown = 1
			elif event.type == KEYUP and event.key == K_SPACE:
				self.isDown = 0
				
		return float(self.isDown)
		
	def quit(self):
		pass
		
class AnalogMuscleControls():
	def __init__(self):
		#channel to use
		displayString('Connecting to Microcontroller...')
		self.channel = 1
		
		#strings to show user
		messageAndOutputs = [	('Relax your muscle, gathering data in %s', 0.0),
								('Tense to 50%%, gathering data in %s', 0.5),
								('Tense to 100%%, gathering data in %s', 1.0)]
		
		message_gathering = "Gathering data..."
		message_complete = 'All done, relax while the system trains'
		
		warnTime = 2
		gatherTime = 2
		
		#some variables to collect training data
		self.data = []
		self.currentOutput = [0.0]
		self.saveData = False
		
		self.ser = continuousMuscleTesting.SerialCommunication(self.__trainCallback)	
		self.ser.Start(1<<self.channel)	#single channel, specified above
		
		for message, output in messageAndOutputs:
			for deciSecondsLeft in range(warnTime * 10, 0, -1):
				displayString(message % str(deciSecondsLeft / 10.0)[:3])
				fpsClock.tick(10)
			
			self.currentOutput = [output]
			self.saveData = True
			
			displayString(message_gathering)
			time.sleep(gatherTime)
			
			self.saveData = False
		
		self.ser.Stop()
		self.ser = None
		
		displayString(message_complete)
		time.sleep(2)#to make sure the system has released the bluetooth connection
		
		self.model = continuousMuscleTesting.getModelFromData(self.data)
		
		self.currentInput = None 	#just to have something there
		self.connected = False
		for _ in range(3):	
			try:
				self.ser = continuousMuscleTesting.SerialCommunication(self.__testCallback)	
				self.ser.Start(1<<(self.channel))	#single channel, specified above
				self.connected = True
				while not self.currentInput:	#wait for data to show up before we start trying to process that data
					time.sleep(0.1)
					
				break
			except Exception, e:
				print e
				time.sleep(1)
				
		if not self.connected:
			displayString('Failed to reconnect')
			time.sleep(1)
			quit()
			
	def quit(self):
		if self.ser:
			self.ser.Stop()
	
	def __trainCallback(self, input):
		self.data.append((input, self.currentOutput))
		
	def __testCallback(self, input):
		#save the input so we can process it to get the output in the main application loop
		self.currentInput = input
		
	def getUpAccel(self, events = []):
		output = self.model.getOutput(self.currentInput)
		tenseness = output[0]
		if tenseness < 0:
			tenseness = 0
		elif tenseness > 1.0:
			tenseness = 1.0
		
		return tenseness
		
class DigitalMuscleControls():
	def __init__(self):
		#train the system
		pass
	
	def getUpAccel(self, events = []):
		pass
		
	def quit(self):
		pass
		
class CaveGeneration():
	def __init__(self):
		self.top = 20
		self.caveHeight = SCREEN_HEIGHT - 100
		
	def getNextDims(self):
		self.top = int(self.top + CAVE_SLOPE * (random.random()* 1000 - 500))
		if self.top < 0:
			self.top = 0
		if self.top + self.caveHeight > SCREEN_HEIGHT:
			self.top = SCREEN_HEIGHT - self.caveHeight
			
		return (self.top, self.top + self.caveHeight)
		
controlType = ControlType.MUSCLE_ANALOG

pygame.init()

fpsClock = pygame.time.Clock()

SCREEN_HEIGHT = 480
SCREEN_WIDTH = 640
HELI_SPEED = 2
HELI_X = SCREEN_WIDTH / 3
CAVE_SPEED = 5

DOWN_ACCEL = 0.5
CAVE_SLOPE = 0.01
HELI_MAX_SPEED = 5

windowSurfaceObj = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Helicopter')

backgroundColor = pygame.Color(0, 0, 0)
caveColor = pygame.Color(0, 255, 0)
scoreColor = pygame.Color(255, 0, 0)
fontObj = pygame.font.Font('freesansbold.ttf', 32)
smallFontObj = pygame.font.Font('freesansbold.ttf', 20)

#reference for image:http://www.how-to-draw-funny-cartoons.com/cartoon-helicopter.html
heliImg = pygame.image.load('cartoon-helicopter-7.png')

caveGenerator = CaveGeneration()
if controlType == ControlType.KEYBOARD:
	controls = KeyboardControls()
elif controlType == ControlType.MUSCLE_ANALOG:
	controls = AnalogMuscleControls()
elif controlType == ControlType.MUSCLE_DIGITAL:
	controls = DigitalMuscleControls()
	
while True:	#keep repeating the game until the user wants to quit

	caveIndex = 0
	caveSpots = [caveGenerator.getNextDims() for _ in range(SCREEN_WIDTH)]

	heliHeight = SCREEN_HEIGHT/2
	heliSpeed = 0

	gameOver = False
	score = 0

	startTime = datetime.now()

	while True:
		elapsed = (datetime.now() - startTime)
		score = int(elapsed.total_seconds() * 10 + elapsed.microseconds / 100000)
		#draw stuff
		windowSurfaceObj.fill(backgroundColor)
		
		#draw the heli
		windowSurfaceObj.blit(heliImg, (HELI_X, SCREEN_HEIGHT - heliHeight))
		
		#draw the cave
		pixArr = pygame.PixelArray(windowSurfaceObj)
		
		for x in range(SCREEN_WIDTH):
			slice = caveSpots[(caveIndex+x) % SCREEN_WIDTH]
			for y in range(slice[0]) + range(slice[1], SCREEN_HEIGHT):
				pixArr[x][y] = caveColor
		del pixArr
				
		scoreSurface = fontObj.render(str(score), False, scoreColor)
		scoreRect = scoreSurface.get_rect()
		scoreRect.topleft = (10, 10)
		windowSurfaceObj.blit(scoreSurface, scoreRect)
				
		#get events
		events = pygame.event.get()
		for event in events:
			if event.type == QUIT:
				quit()
			elif event.type == KEYDOWN:
				if event.key == K_ESCAPE:
					quit()
		
		#get movement of copter
		accel = controls.getUpAccel(events) - DOWN_ACCEL
		heliSpeed += accel
		if heliSpeed > HELI_MAX_SPEED:
			heliSpeed = HELI_MAX_SPEED
		elif heliSpeed < -HELI_MAX_SPEED:
			heliSpeed = -HELI_MAX_SPEED;
			
		heliHeight += heliSpeed * HELI_SPEED
		
		#advance the screen
		for _ in range(CAVE_SPEED):
			caveIndex += 1
			caveIndex %= SCREEN_WIDTH
			caveSpots[caveIndex] = caveGenerator.getNextDims()
		
		#check for endgame stuff
		
		
		#for x in range(HELI_X, HELI_X + heliImg.get_width()):
		
		slice = caveSpots[(caveIndex+HELI_X + heliImg.get_width() / 2) % SCREEN_WIDTH]
		if SCREEN_HEIGHT - heliHeight - heliImg.get_height()/2 < slice[0] or SCREEN_HEIGHT - heliHeight + heliImg.get_height()/2 > slice[1]:
			gameOver = True
			#break
				
		if gameOver:
			break
		
		#draw and wait
		pygame.display.update()
		fpsClock.tick(30)

	#print game over and prompt for quit / replay input
	
	gameOverSurface = fontObj.render(str('Game Over'), False, scoreColor)
	gameOverRect = gameOverSurface.get_rect()
	gameOverRect.center = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
	windowSurfaceObj.blit(gameOverSurface, gameOverRect)
	pygame.display.update()
	
	replaySurface = smallFontObj.render(str('Pressed Enter to replay, ESC to quit'), False, scoreColor)
	replayRect = replaySurface.get_rect()
	replayRect.center = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 30)
	windowSurfaceObj.blit(replaySurface, replayRect)
	pygame.display.update()
	
	#figure out if the user wants to replay or quit
	replay = False
	while not replay:
		events = pygame.event.get()
		for event in events:
			if event.type == QUIT:
				quit()
			elif event.type == KEYDOWN:
				if event.key == K_ESCAPE:
					quit()
				elif event.key == K_RETURN:
					replay = True
				
	