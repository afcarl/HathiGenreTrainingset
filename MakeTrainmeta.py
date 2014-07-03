
import os, sys
import SonicScrewdriver as utils

rowindices, columns, metadata = utils.readtsv("/Users/tunder/Dropbox/pagedata/metascrape/EnrichedMetadata.tsv")

sourcedir = "/Users/tunder/Dropbox/pagedata/newfeatures/oldfeatures/"

dirlist = os.listdir(sourcedir)

htids = list()

ctr = 0
with open("/Users/tunder/Dropbox/pagedata/trainingmeta.tsv", mode="w", encoding="utf-8") as f:
	for filename in dirlist:

	    if len(filename) > 7 and not filename.startswith("."):
	        stripped = filename[:-7]
	        htid = utils.pairtreelabel(stripped)
	        outline = ""
	        for column in columns:
	        	outline = outline + metadata[column][htid] + '\t'
	        f.write(outline + "\n")
