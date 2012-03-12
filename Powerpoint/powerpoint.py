import binaryMuscleTesting
import keyEvent
import svmClassifier
from datetime import datetime
import functools
import serialCom

channels = 3 #1 | 2
minDelayBetweenEvents = 1.0

lastChange = datetime.now()

def powerPointCallback(output):
	global lastChange
	
	if output[0] and output[1]:
		print 'predicting both forward and back...'

	if output[0] or output[1]:
		timeDif = datetime.now() - lastChange
		if timeDif.total_seconds() > minDelayBetweenEvents:
			lastChange = datetime.now()
			if output[0]:
				keyEvent.keyForward()
			elif output[1]:
				keyEvent.keyBack()

def main():
	global channels
	
	trainingData = binaryMuscleTesting.getTrainingData(channels)
	model = svmClassifier.getClassifyData(trainingData)
	classifier = functools.partial(svmClassifier.classifyFunction, model, callback = powerPointCallback)
	
	ser = serialCom.SerialCommunication(classifier)
	ser.Start(channels)
	
	print 'Hit enter to stop'
	s = raw_input()
	ser.Stop()
	
if __name__ == "__main__":
	main()