# Generate Cotraining Set

# This script uses a set of volumes already classified and sorted by a model
# in order to generate additional training data for a new model.

import SonicScrewdriver as utils
from shutil import copyfile

import os, sys

directorylist = os.listdir("/Users/tunder/Dropbox/pagedata/pagemaps/")

toget = list()
for filename in directorylist:
	if filename.endswith(".tsv"):
		toget.append(filename[:-4])

featuredir = "/Volumes/TARDIS/work/cotrain/active/pagefeatures/"

for htid in toget:

	featuresource = "/Volumes/TARDIS/work/cotrain/pagefeatures/" + htid + ".pg.tsv"
	featuredestination = featuredir + htid + ".pg.tsv"
	copyfile(featuresource, featuredestination)

	genresource = "/Users/tunder/Dropbox/pagedata/pagemaps/" + htid + ".tsv"
	genredestination = "/Volumes/TARDIS/work/cotrain/active/genremaps/" + htid + ".map"
	with open(genresource, mode="r", encoding = "utf-8") as f:
		filelines = f.readlines()

	with open(genredestination, mode="w", encoding = "utf-8") as f:
		for line in filelines[1:]:
			f.write(line)
