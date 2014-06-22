# DataSorter.py
# Takes training data produced by five different people and
# collates it to produce a consensus model, while
# producing statistics about inter-rater reliability.

from zipfile import ZipFile
import sys, os
import SonicScrewdriver as utils

rootpath = "/Users/tunder/Dropbox/pagedata/deprecated/"
folderlist = ["Jonathan", "Lea", "Nicole", "Shawn", "Ted"]

def addgenre(agenre, thedictionary):
	if agenre in thedictionary:
		thedictionary[agenre] += 1
	else:
		thedictionary[agenre] = 1

	return thedictionary

translator = {'subsc' : 'front', 'argum': 'non', 'pref': 'non', 'aut': 'non', 'bio': 'non', 'toc': 'front', 'title': 'front', 'bookp': 'front', 'bibli': 'back', 'gloss': 'back', 'epi': 'fic', 'errat': 'non', 'notes': 'non', 'ora': 'non', 'let': 'non', 'trv': 'non', 'lyr': 'poe', 'nar': 'poe', 'vdr': 'dra', 'pdr': 'dra', 'clo': 'dra', 'impri': 'front', 'libra': 'back', 'index': 'back'}

def translate(agenre):
	global translator

	if agenre in translator:
		return translator[agenre]
	else:
		return agenre

genrecounts = dict()

volumesread = dict()

for folder in folderlist:
	thispath = os.path.join(rootpath, folder)
	filelist = os.listdir(thispath)
	for afile in filelist:
		if afile.endswith("maps.zip"):
			filepath = os.path.join(thispath, afile)
			with ZipFile(filepath, mode='r') as zf:
				for member in zf.infolist():

					if not member.filename.endswith('/') and not member.filename.endswith("_Store") and not member.filename.startswith("_"):
						datafile = ZipFile.open(zf, name=member, mode='r')
						filelines = datafile.readlines()
						filelines[0] = filelines[0].rstrip()
						htid = filelines[0].decode(encoding="UTF-8")
						thismap = list()
						counter = 0
						for line in filelines[1:]:
							line = line.decode(encoding="UTF-8")
							line = line.rstrip()
							fields = line.split("\t")
							if int(fields[0]) != counter:
								print("error\a")
							counter += 1
							thisgenre = fields[1]
							thismap.append(thisgenre)
							generalized = translate(thisgenre)
							genrecounts = addgenre(generalized, genrecounts)


						if htid in volumesread:
							volumesread[htid].append((folder,thismap))
							# Note that we append a twotuple, of which the first element is the folder string
							# and the second, the map itself. We will use the folder ID to give preference to
							# ratings by me (Ted).
						else:
							volumesread[htid] = [(folder, thismap)]

def comparelists(firstmap, secondmap, genremistakes):
	assert len(firstmap) == len(secondmap)
	length = len(firstmap)
	divergence = 0.0

	for i in range(length):
		if firstmap[i] == secondmap[i]:
			continue

		generalizedfirst = translate(firstmap[i])
		generalizedsecond = translate(secondmap[i])

		if generalizedfirst == generalizedsecond:
			pass
		else:
			divergence += 1
			addgenre(generalizedfirst, genremistakes)
			addgenre(generalizedsecond, genremistakes)

	return divergence

genremistakes = dict()
volumepercents = dict()
overallcomparisons = 0
overallagreement = 0

badvols = ["njp.32101072911116", "nyp.33433069339749", "hvd.hwjsgk"]

for key, listoftuples in volumesread.items():

	htid = key

	if htid in badvols:
		continue

	nummaps = len(listoftuples)

	lengthofvolume = len(listoftuples[0][1])

	if nummaps == 1:
		continue

	# That's admittedly opaque, but it's the length of the map part of
	# the first maptuple in listoftuples.

	if nummaps == 2:
		graphlinks = 1
	else:
		graphlinks = 3

	potentialcomparisons = graphlinks * lengthofvolume
	totaldivergence = 0
	sanitycheck = 0

	alreadychecked = list()
	for reading in listoftuples:
		readera = reading[0]
		for anotherreading in listoftuples[1:]:
			readerb = anotherreading[0]
			alreadychecked.append((readerb, readera))
			if readera == readerb or (readera, readerb) in alreadychecked:
				continue
			else:
				genrelistA = reading[1]
				genrelistB = anotherreading[1]
				divergence = comparelists(genrelistA, genrelistB, genremistakes)
				totaldivergence += divergence
				sanitycheck += 1

	assert graphlinks == sanitycheck

	agreement = (potentialcomparisons - totaldivergence)
	agreementpercent = agreement / potentialcomparisons
	volumepercents[htid] = agreementpercent
	overallcomparisons += potentialcomparisons
	overallagreement += agreement

print("Average human agreement: " + str(overallagreement / overallcomparisons))

with open("/Users/tunder/Dropbox/pagedata/interrater/HumanAgreement.tsv", mode="w", encoding = "utf-8") as f:
	f.write("htid\tagreement\n")
	for key, value in volumepercents.items():
		outline = utils.pairtreelabel(key) + "\t" + str(value) + "\n"
		f.write(outline)









