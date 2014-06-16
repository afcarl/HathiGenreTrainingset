# Generate Cotraining Set

# This script uses a set of volumes already classified and sorted by a model
# in order to generate additional training data for a new model.

import SonicScrewdriver as utils
from shutil import copyfile

indices, columns, metadata = utils.readtsv("/Volumes/TARDIS/work/cotrain/sortedcotrain.tsv")

toget = indices[-200:]

toget = [utils.pairtreefile(x) for x in toget]

genredir = "/Volumes/TARDIS/work/cotrain/top200/genremaps/"
featuredir = "/Volumes/TARDIS/work/cotrain/top200/pagefeatures/"

for htid in toget:

	featuresource = "/Volumes/TARDIS/work/cotrain/pagefeatures/" + htid + ".pg.tsv"
	featuredestination = "/Volumes/TARDIS/work/cotrain/top200/pagefeatures/" + htid + ".pg.tsv"
	copyfile(featuresource, featuredestination)

	genresource = "/Volumes/TARDIS/work/cotrain/predictions/" + htid + ".predict"
	genredestination = "/Volumes/TARDIS/work/cotrain/top200/genremaps/" + htid + ".map"
	with open(genresource, mode="r", encoding = "utf-8") as f:
		filelines = f.readlines()

	with open(genredestination, mode="w", encoding = "utf-8") as f:
		for line in filelines:
			line = line.rstrip()
			fields = line.split("\t")
			page = fields[0]. split(",")[-1]
			genre = fields[2]
			outline = page + '\t' + genre + '\n'
			f.write(outline)
