# Triadifier

import numpy as np
from Coalescer import Volume
from Coalescer import Chunk

genrelist = ["begin", "end", "ads", "bio", "dra", "fic", "poe", "non", "front", "back"]

def genresequal(truegenre, predictedgenre):
    arethesame = ["bio", "non"]
    if truegenre == predictedgenre:
        return True
    elif truegenre in arethesame and predictedgenre in arethesame:
        return True
    else:
        return False

def genrevectorizer(genre):
	global genrelist

	''' Converts a single nominal feature into a vectorized list of ten
	numeric features, all of which will be zero except for the 1 corresponding
	to the actual genre.'''

	vectorized = [0] * 10
	# Using list rather than numpy array because this will be dynamic array.

	if genre in genrelist:
		idx = genrelist.index(genre)
	else:
		print("Error: Genre " + genre + " not found in genrevectorizer.")
		idx = 0

	vectorized[idx] = 1
	return vectorized

class Volume:

	def __init__(self, listofgenres):
		self.initialsequence = listofgenres
		self.numpages = len(self.initialsequence)
		self.inferredsequence = [x for x in self.initialsequence]
		self.makechunks()
		self.numchunks = len(self.chunklist)

	def makechunks(self):
		chunks = list()
		currentgenre = "nonexistent starting genre"

		for index, genre in enumerate(self.inferredsequence):
			if genre != currentgenre:

				if index > 0:
					currentchunk.clip(index)
					chunks.append(currentchunk)

				currentgenre = genre
				currentchunk = Chunk(genre, index)

		currentchunk.clip(self.numpages)
		if currentchunk.chunksize > 0:
			chunks.append(currentchunk)

		self.chunklist = chunks
		self.numchunks = len(chunks)
		return True

	def getsequence(self):
		return self.inferredsequence

	def convert_to_genre(self, startnum, endnum, genre):

		if startnum < 0 or endnum > self.numpages:
			return False
		else:
			for i in range(startnum, endnum):
				self.inferredsequence[i] = genre
			return True

	def getchunklist(self):
		return self.chunklist

class Chunk:

	def __init__(self, genre, pagenum):
		self.genretype = genre
		self.startpage = pagenum

	def clip(self, pagenum):
		self.endpage = pagenum
		self.chunksize = self.endpage - self.startpage

	def getlen(self):
		length = self.endpage - self.startpage
		if length > 0:
			return length
		else:
			return 1

	def averagedissent(self, dissentseq):
		if self.genretype == "begin" or self.genretype == "end":
			return 1
			# because these chunks will have start and end pages
			# that are not in the sequence
		else:
			total = 0
			for i in range(self.startpage, self.endpage):
				total += dissentseq[i]
			average = total / self.getlen()
			return average

	def averageprob(self, pageprobs):
		if self.genretype == "begin" or self.genretype == "end":
			return 1
			# because these chunks may have no prob or len
		else:
			total = 0
			for i in range(self.startpage, self.endpage):
				total += pageprobs[i][self.genretype]
			average = total / self.getlen()
			return average

class Triad:

	def __init__(self, chunktuple):
		# We expect the chunktuple to be a three-tuple of chunks.

		self.previous = chunktuple[0]
		self.central = chunktuple[1]
		self.next = chunktuple[2]

	def genrefeatures(self):
		firstten = genrevectorizer(self.previous.genretype)
		secondten = genrevectorizer(self.central.genretype)
		thirdten = genrevectorizer(self.next.genretype)

		return firstten + secondten + thirdten
		# Note that these are lists, not numpy arrays, so this returns a list of
		# thirty elements.

	def lengthfeatures(self):

		features = [0] * 6
		features[0] = self.previous.getlen()
		features[1] = self.central.getlen()
		features[2] = self.next.getlen()
		features[3] = features[0] / features[1]
		features[4] = features[2] / features[1]
		if genresequal(self.previous.genretype, self.next.genretype):
			features[5] = (features[0] + features[2]) / features[1]

		return features

	def dissentfeatures(self, dissentseq):

		features = [0] * 3
		features[0] = self.previous.averagedissent(dissentseq)
		features[1] = self.central.averagedissent(dissentseq)
		features[2] = self.next.averagedissent(dissentseq)

		return features

	def runnerupfeatures(self, runnersup):
		features = [0] * 2

		start = self.central.startpage
		end = self.central.endpage

		equalsprev = 0
		equalsnext = 0

		for i in range(start, end):
			if genresequal(runnersup[i], self.previous.genretype):
				equalsprev += 1
			if genresequal(runnersup[i], self.next.genretype):
				equalsnext += 1

		features[0] = equalsprev / self.previous.getlen()
		features[1] = equalsnext / self.next.getlen()
		# Note that getlen() is defined to avoid zero
		# values, so there is no div-by-zero problem here.

		return features

	def prevequalsnext(self):
		features = [0]

		if genresequal(self.previous.genretype, self.next.genretype):
			features[0] = 1

		return features

	def probafeatures(self, pageprobs):
		features = [0] * 3
		features[0] = self.previous.averageprob(pageprobs)
		features[1] = self.central.averageprob(pageprobs)
		features[2] = self.next.averageprob(pageprobs)

		return features

	def getclass(self, groundtruth):

		start = self.central.startpage
		end = self.central.endpage

		reallyprev = 0
		reallynext = 0
		reallyitself = 0

		for i in range(start, end):
			if groundtruth[i] == self.previous.genretype:
				reallyprev += 1
			if genresequal(groundtruth[i], self.central.genretype):
				reallyitself += 1
			if groundtruth[i] == self.next.genretype:
				reallynext += 1

		majority = self.central.getlen() / 2
		if reallyitself >= majority:
			classval = 0
		elif reallyprev > majority or reallynext > majority:
			if reallyprev > reallynext:
				classval = 1
			else:
				classval = 2
		else:
			classval = 0

		return classval

# List of features for each triad:
# 0-9. genre of prev chunk (vectorized to 10 features)
# 10-19. genre of this chunk (vectorized to 10)
# 20-29. genre of next chunk (vectorized to 10)
# 30. length of prev chunk
# 31. length of this chunk
# 32. length of next chunk
# 33. avg dissent, prev chunk
# 34. avg dissent, this chunk
# 35. avg dissent, next chunk
# 36. percent of runners-up that = prev
# 37. percent of runners-up that = next
# 38. does prev equal next?
# 39. avg prob of previous genre
# 40. avg prob of this genre
# 41. avg prob of next genre
# 42. percent pages in this vol predicted to have prev genre
# 43. percent pages in this vol predicted to have this genre
# 44. percent pages in this vol predicted to have next genre

def gettriads(predictedgenres, runnersup, pageprobs, dissentseq, groundtruth):
	''' Receives five lists, each of which contains information keyed to page
	sequences in a volume. Returns a list-of-lists of features (keyed to *triads*
	rather than pages) plus a list of classes for those triads, where a "class"
	indicates whether the central part of the triad should 0) be unchanged,
	1) be changed to the genre of the previous chunk, or 2) be changed to the
	genre of the next chunk.
	'''

	assert len(dissentseq) == len(predictedgenres)
	assert len(pageprobs) == len(predictedgenres)
	assert len(runnersup) == len(predictedgenres)
	#Really all the arguments should have the same length.

	thisvolume = Volume(predictedgenres)
	chunklist = thisvolume.getchunklist()

	beginchunk = Chunk("begin", 0)
	beginchunk.endpage = 0
	chunklist.insert(0, beginchunk)
	endchunk = Chunk("end", len(predictedgenres))
	endchunk.endpage = len(predictedgenres)
	chunklist.append(endchunk)

	triadlist = list()

	for i in range(1, len(chunklist)-1):
		newtriad = Triad((chunklist[i-1], chunklist[i], chunklist[i+1]))
		triadlist.append(newtriad)

	featuresfortriads = list()
	classesfortriads = list()
	instructions = list()

	for tri in triadlist:
		instructiontuple = (tri.central.startpage, tri.central.endpage, tri.previous.genretype, tri.next.genretype)
		instructions.append(instructiontuple)
		# This information will tell us what to change if one of the triads is
		# recognized as needing conversion.

		features = tri.genrefeatures() + tri.lengthfeatures() + tri.runnerupfeatures(runnersup) + tri.prevequalsnext() + tri.probafeatures(pageprobs)
		# Those are all regular lists, so we're just concatenating them.

		# morefeatures = [0] * 3
		# morefeatures[0] = predictedgenres.count(tri.previous.genretype) / len(predictedgenres)
		# morefeatures[1] = predictedgenres.count(tri.central.genretype) / len(predictedgenres)
		# morefeatures[2] = predictedgenres.count(tri.next.genretype) / len(predictedgenres)
		# features = features + morefeatures

		featuresfortriads.append(features)

		classesfortriads.append(tri.getclass(groundtruth))

	return featuresfortriads, classesfortriads, instructions

















