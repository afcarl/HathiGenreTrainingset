import os
import SonicScrewdriver as utils

folder = "/Users/tunder/Dropbox/pagedata/thirdfeatures/pagefeatures/"
files = os.listdir(folder)

validfiles = set()
for filename in files:
	if not filename.startswith(".") and len(filename) > 7:
		filename = filename[:-7]
		validfiles.add(filename)

otherfolder = "/Volumes/TARDIS/output/slices/"

slices = os.listdir(otherfolder)
slicefiles = set()

for aslice in slices:
	if aslice.startswith("."):
		continue
	with open(otherfolder + aslice, encoding="utf-8") as f:
		fl = f.readlines()
	for line in fl:
		line = line.rstrip()
		line = utils.pairtreefile(line)
		slicefiles.add(line)

print(slicefiles.intersection(validfiles))


