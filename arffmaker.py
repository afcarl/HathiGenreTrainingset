# arffmaker.py

import sys, os
import SonicScrewdriver as utils
from shutil import copyfile

with open("/Users/tunder/Dropbox/pagedata/activelearn/sourcefile.txt", mode="r", encoding="utf-8") as f:
	filelines = f.readlines()

files = list()
for line in filelines:
	files.append(line.rstrip())

with open("/Users/tunder/Dropbox/pagedata/activelearn/learn1.arff", mode="w", encoding="utf-8") as f:
	f.write("% List of files in associated folder.\n")
	f.write("% Does not really use arff format.\n")
	f.write("\n")
	f.write("@RELATION learn1\n\n")
	f.write("@ATTRIBUTE htid string\n")
	f.write("@ATTRIBUTE endpg numeric\n")
	f.write("@ATTRIBUTE startpgpart numeric\n")
	f.write("@ATTRIBUTE endpgpart numeric\n")
	f.write("@ATTRIBUTE probability numeric\n")
	f.write("\n")

	for afile in files:
		outline = utils.pairtreefile(afile) + ",0,0,0,0,0\n"
		f.write(outline)
		sourcepath = "/Volumes/TARDIS/work/cotrain/texts/" + utils.pairtreefile(afile) + ".norm.txt"
		destination = "/Users/tunder/Dropbox/pagedata/activelearn/" + utils.pairtreefile(afile) + ".txt"
		copyfile(sourcepath, destination)
		
