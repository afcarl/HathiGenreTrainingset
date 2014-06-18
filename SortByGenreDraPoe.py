# Sort training data by date of publication

import os, sys
import FileUtils

targetgenres = ["dra", "poe", "vdr", "pdr", "clo", "nar", "lyr"]

rowindices, columns, metadata = FileUtils.readtsv2("/Users/tunder/Dropbox/PythonScripts/hathimeta/ExtractedMetadata.tsv") 

genrepath = "/Users/tunder/Dropbox/pagedata/mixedtraining/genremaps/"
featurepath = "/Users/tunder/Dropbox/pagedata/mixedtraining/pagefeatures/"

genrefiles = os.listdir(genrepath)
featurefiles = os.listdir(featurepath)

HTIDs = list()
targetpercent = dict()

for filename in genrefiles:
	if not filename.endswith(".map"):
		continue
	else:
		parts = filename.split(".map")
		htid = parts[0]
		HTIDs.append(htid)
		# Take the part before the extension as the HTID

		with open(genrepath + filename, mode="r", encoding="utf-8") as f:
			filelines = f.readlines()
		pagecounter = 0
		targetcounter = 0
		for line in filelines:
			pagecounter += 1
			line = line.rstrip()
			fields = line.split('\t')
			if fields[1] in targetgenres:
				targetcounter += 1
		targetpercent[htid] = (targetcounter / pagecounter) * 100

intargetgenre = dict()

for htid in HTIDs:
	dirtyid = FileUtils.pairtreelabel(htid)
	if dirtyid in rowindices:
		genrestring = metadata["genres"][dirtyid]
		genreinfo = genrestring.split(";")
		if "Poems" in genreinfo or "Poetry" in genreinfo or "Drama" in genreinfo:
			intargetgenre[htid] = True
		else:
			intargetgenre[htid] = False
	else:
		print("Missing ID.")

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

	istarget = intargetgenre[htid]
	percent = targetpercent[htid]

	if istarget and percent < 50:
		print(htid + "is anomalous.")

	if istarget or percent > 20:
		movefile(htid, "drapoeset")



