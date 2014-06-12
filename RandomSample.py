##

import os, sys
import SonicScrewdriver as utils
import random

rowindices, columns, metadata = utils.readtsv("/Users/tunder/Dropbox/PythonScripts/hathimeta/ExtractedMetadata.tsv")

initialsample = random.sample(rowindices, 2000)

directorylist = os.listdir("/Users/tunder/Dropbox/pagedata/mixedtraining/pagefeatures")
existingfiles = list()

for filename in directorylist:
	if filename.startswith(".") or filename.startswith("_"):
		continue

	htid = utils.pairtreelabel(filename[0:-7])
	existingfiles.append(htid)

counter = 0
toremove = list()
for htid in initialsample:
	if htid in existingfiles:
		counter +=1
		toremove.append(htid)

print("Found " + str(counter) + " duplicates.")
for htid in toremove:
	initialsample.remove(htid)

genresrepresented = set()
for htid in initialsample:
	genrestring = metadata["genres"][htid]
	genreinfo = genrestring.split(";")
	for genre in genreinfo:
		genresrepresented.add(genre)

print(genresrepresented)

user = input("Use this sample? ")

if user == "y":
	with open("/Users/tunder/Dropbox/pagedata/cotraining.txt", mode="w", encoding = "utf-8") as f:
		for htid in initialsample:
			f.write(htid + '\n')
