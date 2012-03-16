FILENAME = 'highScores.txt'
delim = '\t'

class HighScore():
	def __init__(self, filename = globals()['FILENAME']):
		self.filename = filename
		self.readScores()
		
	def getScores(self, n = 10):
		return self.scores[:n]
		
	def readScores(self):
		file = None
		try:
			file = open(self.filename)
		except IOError as e:
			print 'making new file...'
			
		if file:
			self.scores = [line.strip('\n').split(delim) for line in file]
			file.close()
		else:
			self.scores = []
			
		self.scores.sort(cmp = lambda x, y: cmp(int(x[1]), int(y[1])), reverse = True)
		
	def saveScores(self):
		file = open(self.filename, 'w')
		for name, score in self.scores:
			file.write(name + delim + str(score) + '\n')
			
		file.close()
		
	def addScore(self, username, score):
		self.scores.append((username, score))
		self.scores.sort(cmp = lambda x, y: cmp(int(x[1]), int(y[1])), reverse = True)
		self.saveScores()
		