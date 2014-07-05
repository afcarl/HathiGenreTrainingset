# Sort training data by date of publication

import os, sys
import SonicScrewdriver as utils

def letterpart(locnum):
    if locnum == "<blank>":
        return "<blank>"

    letterstring = ""
    for char in locnum:
        if char.isalpha():
            letterstring += char.upper()
        else:
            break
    if len(letterstring) > 2:
        letterstring = letterstring[:2]

    if len(letterstring) > 1 and letterstring[0] == "N":
        letterstring = "N"
    if len(letterstring) > 1 and letterstring[0] == "V":
        letterstring = "V"

    return letterstring

rowindices, columns, metadata = utils.readtsv("/Users/tunder/Dropbox/pagedata/metascrape/EnrichedMetadata.tsv")

with open("/Users/tunder/Dropbox/pagedata/litlocs.tsv", encoding="utf-8") as f:
    filelines = f.readlines()
litlocs = dict()
for line in filelines:
    line = line.strip()
    fields = line.split('\t')
    litlocs[fields[0]] = int(round(1000 * float(fields[1])))

with open("/Users/tunder/Dropbox/pagedata/biolocs.tsv", encoding="utf-8") as f:
    filelines = f.readlines()
biolocs = dict()
for line in filelines:
    line = line.strip()
    fields = line.split('\t')
    biolocs[fields[0]] = int(round(1000 * float(fields[1])))

genrepath = "/Users/tunder/Dropbox/pagedata/newfeatures/genremaps/"
featurepath = "/Users/tunder/Dropbox/pagedata/newfeatures/pagefeatures/"

genrefiles = os.listdir(genrepath)
featurefiles = os.listdir(featurepath)

HTIDs = list()

for filename in genrefiles:
	if not filename.endswith(".map"):
		continue
	else:
		parts = filename.split(".map")
		htid = parts[0]
		HTIDs.append(htid)
		# Take the part before the extension as the HTID

ficgenre = dict()

for htid in HTIDs:
	dirtyid = utils.pairtreelabel(htid)
	if dirtyid in rowindices:
		genrestring = metadata["genres"][dirtyid]
		genreinfo = genrestring.split(";")

		if "Fiction" in genreinfo or "Novel" in genreinfo:
			ficgenre[htid] = True
		else:
			ficgenre[htid] = False

		callno = metadata["LOCnum"][dirtyid]
		LC = letterpart(callno)

		if LC in litlocs:
			litprob = litlocs[LC]
			print(LC + " lit: " + str(litprob))
		else:
			litprob = 120
			print(LC)

		if LC in biolocs:
			bioprob = biolocs[LC]
			print(LC + " bio: " + str(bioprob))
		else:
			bioprob = 120
			print(LC)

		if litprob > 150 and bioprob < 300:
			ficgenre[htid] = True

ctr = 0
for key, value in ficgenre.items():
	if value:
		ctr += 1

print(ctr)

import shutil
def movefile(htid, destination):
	global genrepath, featurepath
	ingenre = genrepath + htid + ".map"
	outgenre = "/Users/tunder/Dropbox/pagedata/" + destination + "/genremaps/" + htid + ".map"
	shutil.copyfile(ingenre, outgenre)
	infeature = featurepath + htid + ".pg.tsv"
	outfeature = "/Users/tunder/Dropbox/pagedata/" + destination + "/pagefeatures/" + htid + ".pg.tsv"
	shutil.copyfile(infeature, outfeature)

for htid in HTIDs:

	isfiction = ficgenre[htid]

	if isfiction:
		movefile(htid, "lit")
	else:
		movefile(htid, "nonlit")



