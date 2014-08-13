# PageLevelWordCounter

import os, sys

import SonicScrewdriver as utils

sourcedirectory = "/Users/tunder/Dropbox/pagedata/seventhfeatures/pagefeatures/"

dirlist = os.listdir(sourcedirectory)

validnames = list()

for filename in dirlist:
	if not (filename.startswith(".") or filename.startswith("_")):
		validnames.append(filename)

filedict = dict()

for filename in validnames:
	filepath = os.path.join(sourcedirectory, filename)
	pagedict = dict()

	with open(filepath, mode="r", encoding="utf-8") as f:
		filelines = f.readlines()

	for line in filelines:
		line = line.rstrip()
		fields = line.split("\t")

		word = fields[1]
		page = int(fields[0])
		count = int(fields[2])

		if word.startswith("#"):
			count = 0

		if page in pagedict:
			pagedict[page] += count
		else:
			pagedict[page] = count

	htid = filename[0:-7]
	filedict[htid] = pagedict

with open("/Users/tunder/Dropbox/pagedata/seventhfeatures/pagelevelwordcounts.tsv", mode="w", encoding="utf-8") as f:
	f.write("htid\tpage\twordcount\n")
	for htid, pagedict in filedict.items():
		tuplelist = utils.sortvaluesbykey(pagedict)
		counter = 0
		for twotuple in tuplelist:
			pagenum, count = twotuple
			if pagenum < 0:
				continue
			elif pagenum != counter:
				print("pagination anomaly")
			else:
				counter += 1
				outline = htid + "\t" + str(pagenum) + "\t" + str(count) + "\n"
				f.write(outline)



