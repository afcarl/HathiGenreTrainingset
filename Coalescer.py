# Coalesce genres into sequences

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
		return self.endpage - self.startpage

def effectively_equal(genrea, genreb):
	alsothesame = ["back", "index"]
	if genrea == genreb:
		return True
	elif genrea == "fic" and genreb == "bio":
		return True
	elif genrea == "bio" and genreb == "fic":
		return True
	elif genrea == "non" and genreb == "bio":
		return True
	elif genrea == "bio" and genreb == "non":
		return True
	elif genrea == "trv" and (genreb == "bio" or genreb == "non"):
		return True
	elif (genrea == "bio" or genrea == "non") and genreb == "trv":
		return True
	elif genrea in alsothesame and genreb in alsothesame:
		return True
	else:
		return False

def not_suspicious(genrea, genreb):
	'''We take the view that small numbers of front and non pages
	should be permitted to persist next to each other, because this
	is often the case. Also, small numbers of front pages can occur anywhere.'''

	if genrea == "front" and (genreb == "bio" or genreb == "non"):
		return False
	elif (genrea == "bio" or genrea == "non") and genreb == "front":
		return False
	else:
		return True

def find_consensus(genrea, sizea, genreb, sizeb):
	if genrea == genreb:
		return genrea
	elif sizea > sizeb:
		return genrea
	elif sizea < sizeb:
		return genreb
	else:
		return genreb

def closematches(genrea, genreb):
	allthesame = ["fic", "bio", "non"]
	alsothesame = ["back", "index"]
	if genrea in allthesame and genreb in allthesame:
		return True
	elif genrea in alsothesame and genreb in alsothesame:
		return True
	else:
		return False

def coalesce(listofgenres):

	thisvol = Volume(listofgenres)
	thisvol.makechunks()

	if thisvol.numchunks < 3:
		return thisvol.getsequence(), thisvol.numchunks

	changesmade = True

	while changesmade:

		changesmade = False

		triads = list()
		for i in range(1, thisvol.numchunks - 1):
			first = thisvol.chunklist[i-1]
			second = thisvol.chunklist[i]
			third = thisvol.chunklist[i+1]

			if effectively_equal(first.genretype, third.genretype) and not_suspicious(first.genretype, second.genretype):
				threetuple = (first, second, third)
				triads.append(threetuple)

		ratedtriads = list()
		disproportions = list()

		for triad in triads:
			first, second, third = triad
			envelopingtotal = first.chunksize + third.chunksize
			innertotal = second.chunksize

			disproportion = (envelopingtotal / innertotal)

			if innertotal < 3 and disproportion >= 3 or (disproportion >= 2 and closematches(first.genretype, second.genretype)):
				decoratedtriad = (disproportion, triad)
				ratedtriads.append(decoratedtriad)
				disproportions.append(disproportion)
		
		try:
			ratedtriads.sort(reverse = True, key = lambda x: x[0])
		except:
			print("Sorting error with " + str(len(ratedtriads)) + " triads.")
			print(disproportions)

		if len(ratedtriads) > 0:
			decoration, triad = ratedtriads[0]
			first, second, third = triad
			consensus_genre = find_consensus(first.genretype, first.chunksize, third.genretype, third.chunksize)
			thisvol.convert_to_genre(second.startpage, second.endpage, consensus_genre)
			
			changesmade = True

			thisvol.makechunks()

			# for agenre in thisvol.getsequence():
			# 	print(agenre, end = " ")
			# print()

			# user = input("Continue? ")

	return thisvol.getsequence(), thisvol.numchunks










