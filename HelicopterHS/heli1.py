import pygame, sys
from pygame.locals import*
import random
from datetime import datetime
import time
import continuousMuscleTesting
import binaryMuscleTesting
import functools

import highScore

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
		#get the user to train the system
		self.data = []
		self.channel = 2
		
		displayString('Connecting to Bluetooth...')
		
		self.ser = continuousMuscleTesting.SerialCommunication(self.__trainCallback)	
		self.ser.Start(1<<(self.channel-1))	#single channel, specified above
		
		displayString('Tap the SPACE Key a few times')
		
		#wait until we have enough examples of both outputs
		while True:
			outputs = map(lambda x: x[1][0], self.data)
			posCount = sum(outputs)
			negCount = len(outputs) - sum(outputs)
			if min(posCount, negCount) > 50:
				break
				
		self.ser.Stop()
		self.ser = None
		
		displayString('Got enough data, training the system')
		time.sleep(1)
		
		binaryMuscleTesting.saveTrainingData(self.data, 'digitalTrainingData.txt')
		self.model = binaryMuscleTesting.getModelFromData(self.data)
		self.classifyFunction = functools.partial(binaryMuscleTesting.module.classifyFunction, self.model,callback = self.__testCallback)
		
		self.currentInput = None
		self.ser = continuousMuscleTesting.SerialCommunication(self.__testCallback)	
		self.ser.Start(1<<(self.channel-1))	#single channel, specified above
		
		#wait for the system to start up and give some input
		while not self.currentInput:
			time.sleep(0.1)
		
	def __trainCallback(self, input):
		output = binaryMuscleTesting.keyListener.getSpecificKeyOutput(' ')
		self.data.append((input, [output]))
		
	def __testCallback(self, input):
		self.currentInput = input[0]
		
	def getUpAccel(self, events = []):
		return self.currentInput
		
	def quit(self):
		self.ser.Stop()
		
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
		
		
def onCrash():
	gameOverSurface = fontObj.render(str('Game Over'), False, scoreColor)
	gameOverRect = gameOverSurface.get_rect()
	gameOverRect.center = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
	windowSurfaceObj.blit(gameOverSurface, gameOverRect)
	
	nameLine = 'Enter your name: %s'
	name = ''
	while True:
		draw()
		replaySurface = smallFontObj.render(nameLine % name, False, scoreColor)
		replayRect = replaySurface.get_rect()
		replayRect.center = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 30)
		windowSurfaceObj.blit(replaySurface, replayRect)
		pygame.display.update()
		
		#figure out if the user wants to replay or quit
		pressedEnter = False
		events = pygame.event.get()
		for event in events:
			if event.type == QUIT:
				quit()
			elif event.type == KEYDOWN:
				if event.key == K_ESCAPE:
					quit()
				elif event.key == K_RETURN:
					pressedEnter = True
				elif event.key >= pygame.K_a and event.key <= pygame.K_z:
					if len(name) < 20:
						name += chr(event.key)
				
		if pressedEnter:
			break
			
		fpsClock.tick(30)
		
	highScore.addScore(name, score)
	
	#get rid of the previous text
	draw()	
	
	#display previous high scores
	scores = highScore.getScores()
	
	hsSurface = fontObj.render('High Scores', False, scoreColor)
	hsRect = hsSurface.get_rect()
	hsRect.topleft = (80, 10)
	windowSurfaceObj.blit(hsSurface, hsRect)
		
	for i, (hName, hScore) in enumerate(scores):
		hsSurface = smallFontObj.render(hName + ' '*(40 - len(hName) - len(str(hScore))) + str(hScore), False, scoreColor)
		hsRect = hsSurface.get_rect()
		hsRect.topleft = (80, 50 + i * 30)
		windowSurfaceObj.blit(hsSurface, hsRect)
		
	pygame.display.update()
		
	pressedEnter = False
	while not pressedEnter:
		events = pygame.event.get()
		
		for event in events:
			if event.type == QUIT:
				quit()
			elif event.type == KEYDOWN:
				if event.key == K_ESCAPE:
					quit()
				elif event.key == K_RETURN:
					pressedEnter = True
	
controlType = ControlType.KEYBOARD
#controlType = ControlType.MUSCLE_ANALOG
#controlType = ControlType.MUSCLE_DIGITAL

pygame.init()

fpsClock = pygame.time.Clock()
highScore = highScore.HighScore()

SCREEN_HEIGHT = 480
SCREEN_WIDTH = 640
HELI_SPEED = 2
HELI_X = SCREEN_WIDTH / 3
CAVE_SPEED = 5

DOWN_ACCEL = 0.5
CAVE_SLOPE = 0.01
HELI_MAX_SPEED = 5

POWER_PADDING = 20
POWER_WIDTH = 100
POWER_HEIGHT = 30
POWER_OUTLINE_THICKNESS = 3

windowSurfaceObj = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Helicopter')

backgroundColor = pygame.Color(0, 0, 0)
caveColor = pygame.Color(0, 255, 0)
scoreColor = pygame.Color(255, 0, 0)
powerOutlineColor = pygame.Color(255, 0, 255)
powerColor = pygame.Color(255, 0, 0)
fontObj = pygame.font.Font('freesansbold.ttf', 32)
smallFontObj = pygame.font.Font('freesansbold.ttf', 20)

#reference for image:http://www.how-to-draw-funny-cartoons.com/cartoon-helicopter.html
heliImg = pygame.image.load('cartoon-helicopter-7.png')

def draw():	
	#draw stuff
	windowSurfaceObj.fill(backgroundColor)
	
	#draw the heli
	windowSurfaceObj.blit(heliImg, (HELI_X, SCREEN_HEIGHT - heliHeight))
	
	for x in range(SCREEN_WIDTH):
		slice = caveSpots[(caveIndex+x) % SCREEN_WIDTH]
		pygame.draw.line(windowSurfaceObj, caveColor, (x, 0), (x, slice[0]))
		pygame.draw.line(windowSurfaceObj, caveColor, (x, slice[1]), (x, SCREEN_HEIGHT))
	
	scoreSurface = fontObj.render(str(score), False, scoreColor)
	scoreRect = scoreSurface.get_rect()
	scoreRect.topleft = (10, 10)
	windowSurfaceObj.blit(scoreSurface, scoreRect)

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
		draw()
	
		elapsed = (datetime.now() - startTime)
		score = int(elapsed.total_seconds() * 10 + elapsed.microseconds / 100000)
		
		#get events
		events = pygame.event.get()
		for event in events:
			if event.type == QUIT:
				quit()
			elif event.type == KEYDOWN:
				if event.key == K_ESCAPE:
					quit()
		
		#get movement of copter
		accelUp = controls.getUpAccel(events)
		accel = accelUp - DOWN_ACCEL
		heliSpeed += accel
		if heliSpeed > HELI_MAX_SPEED:
			heliSpeed = HELI_MAX_SPEED
		elif heliSpeed < -HELI_MAX_SPEED:
			heliSpeed = -HELI_MAX_SPEED;
			
		heliHeight += heliSpeed * HELI_SPEED
		
		#draw the power / up acceleration meter
		pygame.draw.rect(windowSurfaceObj, powerOutlineColor, (POWER_PADDING, SCREEN_HEIGHT - POWER_PADDING, POWER_WIDTH, -POWER_HEIGHT), 5)
		pygame.draw.rect(windowSurfaceObj, powerColor, (POWER_PADDING + POWER_OUTLINE_THICKNESS, \
					SCREEN_HEIGHT - POWER_PADDING -POWER_OUTLINE_THICKNESS, \
					(POWER_WIDTH - 2* POWER_OUTLINE_THICKNESS) * accelUp , -(POWER_HEIGHT - 2 * POWER_OUTLINE_THICKNESS)))
		
		#advance the screen
		for _ in range(CAVE_SPEED):
			caveIndex += 1
			caveIndex %= SCREEN_WIDTH
			caveSpots[caveIndex] = caveGenerator.getNextDims()
		
		slice = caveSpots[(caveIndex+HELI_X + heliImg.get_width() / 2) % SCREEN_WIDTH]
		if SCREEN_HEIGHT - heliHeight - heliImg.get_height()/2 < slice[0] or SCREEN_HEIGHT - heliHeight + heliImg.get_height()/2 > slice[1]:
			gameOver = True
				
		if gameOver:
			break
		
		#draw and wait
		pygame.display.update()
		fpsClock.tick(30)
		
	onCrash()