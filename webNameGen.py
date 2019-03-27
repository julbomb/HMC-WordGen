#!/usr/bin/env python3
import time
import codecs # open files with "drivers" (utf-8, ascii, etc) for windows (meh) compatibility
import sys
import json
from collections import deque
import random

from http.server import BaseHTTPRequestHandler,HTTPServer
from socketserver import TCPServer
import ssl # For https, when we'll have time to loose

def lPrints(c):
	sys.stdout.write(c)
	sys.stdout.flush()

# Make a random choice with weighted values
# input: {"key1": 1, "key2": 4, "key3": 2}
# output: (example) "key 1"
def weightedChoice(values):
	total = sum(w for c, w in values.items())
	r = random.uniform(0, total)
	upto = 0
	for c, w in values.items():
		if upto + w >= r:
			return c
		upto += w

	# Should never go there
	return values[list(values.keys())[0]]

# Compute  and holds probability for n-gram
# Add words to LetterFreq to build and count n-grams
# Compute probability of all added words
# Use it as a random letter generator (given the ngram-1 previous letter)
class LetterFreq:
	def __init__(self,ngram):
		self.ngram = ngram
		self.ngramCount = 0
		self.valueMap = {}
		self.freqMap = {}

	# Count ngrams
	def addToCount(self,word):
		if self.ngram != 1:
			# $ is starting ! is ending
			word = "$" + word.lower() + "!"

		for i in range(len(word)-(self.ngram-1)):
			# Getting the current n-gram
			current = word[i:i+self.ngram]

			# Access the value map
			currMap = self.valueMap
			currFreqMap = self.freqMap
			for c in current[:-1]:
				# Create freq if not existing
				if c not in currMap:
					currMap[c] = {}
					currFreqMap[c] = {}

				currMap = currMap[c]
				currFreqMap = currFreqMap[c]

			# Create counter if not exist
			if current[-1] not in currMap:
				currMap[current[-1]] = 0
				currFreqMap[current[-1]] = 0.0

			# Update count
			currMap[current[-1]] = currMap[current[-1]]+1

		self.ngramCount = self.ngramCount+len(word)-self.ngram

	# Compute ngram probability (recursively)
	def computeProbability(self):
			self._recurseComputeProb(self.freqMap,self.valueMap)

	# Recursive N-gram calculation
	def _recurseComputeProb(self,freqObj,countObj):
		kList = list(freqObj.keys())
		if len(kList) > 0:
			firstKey = kList[0]
			if isinstance(freqObj[firstKey],dict):
				for k in freqObj:
					self._recurseComputeProb(freqObj[k],countObj[k])
			else:
				for k in freqObj:
					freqObj[k] = countObj[k]/float(self.ngramCount)

	# Pick a random ngram
	def getNewLetter(self,currentWord):
		if len(currentWord) > self.ngram-1:
			current = currentWord[-(self.ngram-1):]
		else:
			current = currentWord

		currentFreq = self.freqMap
		for c in current:
			currentFreq = currentFreq[c]

		return weightedChoice(currentFreq)

	# Save Frequency data to json file
	def saveToFile(self,fn):
		jsonMap = {}

		jsonMap["ngram"] = self.ngram
		jsonMap["ngramCount"] = self.ngramCount
		jsonMap["valueMap"] = self.valueMap
		jsonMap["freqMap"] = self.freqMap

		with open(fn,"w") as file:
			file.write(json.dumps(jsonMap))

	# Load Frequency data to json file
	def loadFromFile(self,fn):
		jsonMap = {}
		with open(fn,"r") as file:
			jsonMap = json.load(file)

		self.ngram = jsonMap["ngram"]
		self.ngramCount = jsonMap["ngramCount"]
		self.valueMap = jsonMap["valueMap"]
		self.freqMap = jsonMap["freqMap"]

# Name generator class
# Loads database, create FreqLetter for all the ngrams ([2-N])
# Generates random names based on ngrams
class NameGen:
	# Constructor name generator
	def __init__(self,ngrams):
		self.ngram = ngrams

	# Initialize NameGenerator using database
	# Optionnal argument, read function:
	# 	if set, use the function to extract town name
	#	eg: file format is "name;otherInfo;otherInfo;...\n"
	#		readFun = lambda line: line.split(";")[0]
	def init(self,database,readFun=None):
		# Generates all the previous n-grams for starting letters
		if self.ngram > 2:
			self.freqHolders = []
			for i in range(2,self.ngram):
				self.freqHolders.append(LetterFreq(i))

		# Loads database
		with open(database,"r") as file:
			for line in file.readlines():
				# Exctract name
				name = ""
				if readFun != None:
					name = readFun(line)
				else:
					name = line[:-1] # For ville.out

				# Add name to all FreqLetters [2-N]
				for i in range(2,self.ngram):
					if len(name)+2 >= i:
						self.freqHolders[i-2].addToCount(name)

		for frq in self.freqHolders:
			frq.computeProbability()

	# Generate a name
	def generate(self):
		# Pick The first letter randomly
		firstLetters = None

		firstLetters = weightedChoice(self.freqHolders[0].freqMap["$"])

		# Take the (ngram-2) next letter given the n-grams
		firstLetters = "$" + firstLetters
		for j in range(3,self.ngram):
			nStartLetter = self.freqHolders[j-2].getNewLetter(firstLetters)
			firstLetters = firstLetters + nStartLetter

			if nStartLetter == "!":
				return firstLetters


		# Beginning of word is set, lets continue !
		word = firstLetters
		stillSomeLetters = True
		while stillSomeLetters:
			# Security
			if len(word) < 50:
				nl = self.freqHolders[-1].getNewLetter(word)
			else:
				nl = "!"
			word = word + nl

			if nl == "!":
				stillSomeLetters = False

		return word

	# Save NameGenerator data to json file
	def saveToFile(self,fn):
		jsonMap = {}

		jsonMap["ngram"] = self.ngram

		with open(fn,"w") as file:
			file.write(json.dumps(jsonMap))
		
		for freq in self.freqHolders:
			freq.saveToFile(fn + "_freq_"+str(freq.ngram))

	# load NameGenerator data from json file
	def loadFromFile(self,fn):
		jsonMap = {}
		with open(fn,"r") as file:
			jsonMap = json.load(file)

		self.ngram = jsonMap["ngram"]
		self.freqHolders = []

		for i in range(2,self.ngram):
			self.freqHolders.append(LetterFreq(i))
			self.freqHolders[-1].loadFromFile(fn + "_freq_"+str(self.freqHolders[-1].ngram))


# Singelton for NameGenerator (facilitates uses as a webserver)
class SingletonNameGen:
	nameGenerator = None

	# Init singleton
	@staticmethod
	def initFromDatabase(ngram,database):
		SingletonNameGen.nameGenerator = NameGen(ngram)
		SingletonNameGen.nameGenerator.init(database)

	def initFromNgram(jsonFilenamePrefix):
		SingletonNameGen.nameGenerator = NameGen(ngram)
		SingletonNameGen.nameGenerator.loadFromFile(jsonFilenamePrefix)

	# Call generates method
	@staticmethod
	def gen():
		s = SingletonNameGen.nameGenerator.generate()[1:-1]
		return s

# Custom HTTP server
# Respond to 3 specific requests :
#  - "/name": generates random town name
#  - "/": send home page
#  - "/favicon.png": sends favicon file
# All "/name", "/", and unwanted requests are logged.
class CustomHTTPHandler(BaseHTTPRequestHandler):
	# Handle HTTp request
	def do_GET(self):
		# Request for name generation
		if self.path == "/name":
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			self.wfile.write(bytes(SingletonNameGen.gen(),"utf-8"))

			# Log entry (keeps generation counts)
			with open("log","a") as f:
				f.write("gen,{0},{1}\n".format(time.time(),self.client_address[0]))
		# Request sides files (js, css, favicons, etc); not logged
		elif self.path in ["/fonts/UbuntuMono-R.ttf","/images/background.png","/favicon.png","/css/default_style.css","/scripts/generate.js"]:
			self.send_response(200)

			# Sends mime types
			if self.path.endswith("png"):
				self.send_header("Content-type", "image/png")
			elif self.path.endswith("css"):
				self.send_header("Content-type", "text/css")
			elif self.path.endswith("js"):
				self.send_header("Content-type", "application/javascript")
			elif self.path.endswith("ttf"):
				self.send_header("Content-type", "font/opentype")
			self.end_headers()

			with open("."+self.path,"rb") as f:
				self.wfile.write(bytes(f.read()))
		# Request for home page
		elif self.path == "/":
			self.send_response(200)
			self.send_header("Content-type", "text/html")
			self.end_headers()
			with open("./index.html","r") as f:
				for l in f.readlines():
					self.wfile.write(bytes(l,"utf-8"))

			# Log entry (keeps home pages requests counts)
			with open("log","a") as f:
				f.write("idx,{0},{1}\n".format(time.time(),self.client_address[0]))
		# Nothing else allowed (security precaution, maybe i'm too paranoid)
		else:
			self.send_response(404)
			self.end_headers()

			# Log entry (keeps unwanted visitors counts)
			with open("log","a") as f:
				f.write("{2},{0},{1}\n".format(time.time(),self.client_address[0],self.path))

		print(self.path)

# Web service is running
if __name__ == '__main__':
	# Params
	ngram = 10
	database = "ville.out"
	random.seed()
	hasParam = len(sys.argv) > 0

	if hasParam and "-ngram" in sys.argv:
		i = sys.argv.index("-ngram")
		if len(sys.argv) > i+1:
			# Load namegenerator data
			n = int(sys.argv[i+1])
			print("Set ngram: " + str(n))					
			ngram = n
		else:
			print("Error, need number of ngram")
			exit(1)
	
	t0 = time.time()	
	# Load learning from file
	if hasParam and "-load" in sys.argv:
		i = sys.argv.index("-load")
		if len(sys.argv) > i+1:
			# Load namegenerator data
			fn = sys.argv[i+1]
			print("Loading: " + fn)					
			SingletonNameGen.initFromNgram(fn)
		else:
			print("Error, need filename to load")
			exit(1)
	else:
		# No params, learn from default database
		print("Learning.")
		SingletonNameGen.initFromDatabase(ngram,database)
		
	t1 = time.time()
		
	print("Done in {0}s.".format(round(t1-t0,3)))

	# HTTP Service	
	if hasParam and "-noweb" not in sys.argv:
		print("Start service.")
		server = TCPServer(("0.0.0.0", 8080), CustomHTTPHandler)
		server.timeout = 2.0
		# HTTPS wrapper, need .crt file
		#server.socket = sll.wrap_scoket(server.socket,certfile="./",server_side=True)

		# Serving
		print("Serving...")
		while True:
			server.handle_request()
	# If noweb is specified, you can generate manually
	elif hasParam and "-gen" in sys.argv:
		i = sys.argv.index("-gen")
		if len(sys.argv) > i+1:
			print("-------------")
			nGen = int(sys.argv[i+1])
			for i in range(nGen):
				print(SingletonNameGen.gen())
			print("-------------")			
		else:
			print("Warning, need parameter to generate names")
			
	# Save to file after		
	if hasParam and "-save" in sys.argv:
		i = sys.argv.index("-save")
		if len(sys.argv) > i+1:
			fn = sys.argv[i+1]
			SingletonNameGen.nameGenerator.saveToFile(fn)
		else:
			print("Warning, need filename to save, learning not saved")
