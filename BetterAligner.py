import os, sys
import difflib
import random
from multiprocessing import Pool

def makesequence(filelines):
	thispage = ""
	pageseq = list()

	for line in filelines:
		if line.startswith("<pb>"):
			if not "Estimated percentage of bad pages" in thispage:
				pageseq.append(thispage)
			thispage = ""
		else:
			thispage += line
	if not "IMPLICIT PAGE NUMBER" in thispage and not "UNTYPICAL PAGE" in thispage:
		pageseq.append(thispage)

	return pageseq

def alignsize(string1, string2):
	avgsize = 2 + ((len(string1) + len(string2)) / 2)
	# We add an extra two here, because we want the 1.0 ratio match
	# between two empty strings to mean something, in spite of the fact
	# that the strings have no size

	stringdiff = difflib.SequenceMatcher(a = string1, b = string2)

	alignsize = avgsize * stringdiff.ratio()

	return alignsize

def sequencematches(seq1, seq2):
	forwardwindow = (len(seq2) - len(seq1)) + 3
	backwardwindow = 3

	bypage = dict()

	for idx, page in enumerate(seq1):
		# print(idx)

		startpg = idx - backwardwindow
		if startpg < 0:
			startpg = 0

		endpg = idx + forwardwindow
		if endpg > len(seq2):
			endpg = len(seq2)

		for matchidx in range(startpg, endpg):
			matchpg = seq2[matchidx]
			alignment = alignsize(page, matchpg)

			if idx in bypage:
				bypage[idx].append((alignment, idx, matchidx))
			else:
				bypage[idx] = [(alignment, idx, matchidx)]

			# You might think that idx would not need to be in the tuple value
			# since it's in the key. But we're going to pass this tuple
			# around.

	return bypage

def extracttopmatches(matchdict):
	topmatches = list()

	for key, value in matchdict.items():
		value.sort(reverse = True)
		topmatches.append(value[0])

	topmatches.sort(reverse = True)

	return topmatches

def possiblematch(seq1, old2new, oldpage, newpage):
	succeed = True
	for i in range(oldpage, -1, -1):
		if old2new[i] > newpage:
			succeed = False
	for i in range(oldpage, len(seq1)):
		if old2new[i] > 0 and old2new[i] < newpage:
			succeed = False

	return succeed

def realign_map(maplines, oldpagenums):
	mapseq = list()
	for line in maplines:
		line = line.rstrip()
		fields = line.split('\t')
		mapseq.append(fields[1])

	# Let's do some validation to make sure our assumptions are correct.
	# Oldpagenums should be a sequence of numbers in ascending order, and
	# the highest number should be the highest index in mapseq.

	lastnumber = -1
	for number in oldpagenums:
		if number < lastnumber:
			print("Error!")
			sys.exit()

	assert number + 1 <= len(mapseq)

	newseq = list()

	lastpagenum = -1
	alreadyresolved = ""
	for pagenum in oldpagenums:

		if pagenum > lastpagenum:
			newseq.append(mapseq[pagenum])
			alreadyresolved = ""
			# This resets the flag we use to preserve sequences of inserted
			# pages as the same genre

		else:
			# We have a repeat. This means pages have been inserted in the sequence.
			# We need to get the previous and subsequent genre. Previous genre is
			# the current (repeated) number.

			if (pagenum) >= 0:
				previous = mapseq[pagenum]
			else:
				previous = "front"

			if (pagenum + 1) < len(mapseq):
				thenext = mapseq[pagenum + 1]
			else:
				thenext = "back"

			if previous == thenext:
				insertedgenre = previous
				# That was easy. No conflict.
				# Otherwise ...

			elif len(alreadyresolved) > 0:
				insertedgenre = alreadyresolved
				# If there's a sequence of inserted genres we want to keep them
				# consistent.

			elif previous == "front":
				insertedgenre = "front"
			elif thenext == "back":
				insertedgenre = "back"

			# Those are fairly common cases, because a lot of blank pages
			# are inserted at the beginning or end of the book.

			else:
				insertedgenre = random.sample([previous, thenext], 1)[0]
				# wild guess

			newseq.append(insertedgenre)
			alreadyresolved = insertedgenre
			print(previous + " - " + insertedgenre + " - " + thenext)

		# Whatever we did above, reset lastpagenum as we move to the next
		# item in the iterable.

		lastpagenum = pagenum

	assert len(newseq) == len(oldpagenums)

	outlines = list()
	for idx, genre in enumerate(newseq):
		outline = str(idx) + '\t' + genre + '\n'
		outlines.append(outline)

	return outlines

def main():
	firstfolder = "/Users/tunder/Dropbox/pagedata/newfeatures/texts/"
	secondfolder = "/Users/tunder/Dropbox/pagedata/normtxts/"

	secondfiles = set(os.listdir(secondfolder))

	validfiles = [x for x in secondfiles if not x.startswith(".")]

	firstfiles = os.listdir(firstfolder)
	fixedfiles = list()
	for x in firstfiles:
		x = x.replace("norm.txt", "") + ".norm.txt"
		fixedfiles.append(x)

	missing = [x for x in validfiles if x not in fixedfiles]

	if len(missing) > 0:
		print("Error -- missing files.")
		sys.exit()

	filenamedict = dict()
	for filename in validfiles:
		shortpart = filename.replace(".norm.txt", "")
		for otherfilename in firstfiles:
			if otherfilename.startswith(shortpart):
				filenamedict[filename] = otherfilename

	print(len(filenamedict))

	mapoutput = "/Users/tunder/Dropbox/pagedata/seventhfeatures/genremaps/"
	alreadymapped = os.listdir(mapoutput)
	dontprocess = set()
	for filename, value in filenamedict.items():
		if (filename[:-9] + ".map") in alreadymapped:
			dontprocess.add(filename)

	tuplelist = list()
	for key, value in filenamedict.items():
		if not key in dontprocess:
			tuplelist.append((key, value))

	print(len(tuplelist))

	for atuple in tuplelist:
		realign_file(atuple)
	print("Done.")

def realign_file(filetuple):

	filename, otherfilename = filetuple
	oldmapinput = "/Users/tunder/Dropbox/pagedata/thirdfeatures/genremaps/"
	mapoutput = "/Users/tunder/Dropbox/pagedata/seventhfeatures/genremaps/"
	firstfolder = "/Users/tunder/Dropbox/pagedata/newfeatures/texts/"
	secondfolder = "/Users/tunder/Dropbox/pagedata/normtxts/"
	firstpath = firstfolder + otherfilename
	secondpath = secondfolder + filename

	with open(firstpath, encoding = "utf-8") as f1:
		fl1 = f1.readlines()

	with open(secondpath, encoding = "utf-8") as f2:
		fl2 = f2.readlines()

	seq1 = makesequence(fl1)
	seq2 = makesequence(fl2)

	mapname = filename[:-9] + ".map"
	with open(oldmapinput + mapname, encoding = "utf-8") as f:
		maplines = f.readlines()

	print()
	print(filename, len(seq1), len(seq2))
	print(len(maplines))

	assert len(maplines) == len(seq1)

	matchesbypage = sequencematches(seq1, seq2)
	topmatches = extracttopmatches(matchesbypage)

	old2new = [-1] * len(seq1)
	# We're going to find a match in the newsequence (seq2) for every page
	# in seq1. Until we do it's tagged as -1.

	for match in topmatches:
		closeness, oldpage, newpage = match
		# Which page has the top match

		thispageslist = matchesbypage[oldpage]
		# Get all the matches for that page

		for match in thispageslist:
			closeness, oldpage, newpage = match
			matchworks = possiblematch(seq1, old2new, oldpage, newpage)
			# Make sure that this match wouldn't violate the sequentiality
			# of existing matches.

			if matchworks:
				old2new[oldpage] = newpage
				break

	# Now, in theory, we have matches for all the old pages, and they are
	# sequential within newpages. Check this.

	lastpg = -1
	for newpg in old2new:
		if newpg < lastpg:
			print("Error! Sequence violated.")
		if newpg < 0:
			print("Error! Unmatched page.")

	# Now to deal with the pesky problem of unmatched newpages.

	new2old = [-1] * len(seq2)
	for idx, page in enumerate(seq2):
		if idx in old2new:
			theoldpage = old2new.index(idx)
			new2old[idx] = theoldpage
		else:
			lowerbound = 0
			for i in range(idx, -1, -1):
				if i in old2new:
					lowerbound = old2new.index(i)
					break
			upperbound = len(seq1) -1
			for i in range(idx, len(seq2)):
				if i in old2new:
					upperbound = old2new.index(i)
					break

			if lowerbound == upperbound:
				# This page is an insertion between two page that
				# match the same oldpg.
				new2old[idx] = lowerbound
			elif (upperbound - lowerbound) == 1:
				# This page is again an insertion
				new2old[idx] = lowerbound
			elif (upperbound - lowerbound) == 2:
				# We have a situation where the nearest newpages that match
				# in oldpage match pages that are separated by two
				# steps in the oldpage sequence. This should not really happen,
				# but okay. We can solve this arbitrarily.
				new2old[idx] = lowerbound + 1
			else:
				print("Problematic situation.")
				print("Lower bound: " + str(lowerbound))
				print("Upper bound: " + str(upperbound))
				# We have a situation where the nearest newpages match pages
				# that are separated by multiple pages in the oldpg sequence.
				# We're going to fill from the lower end, but this really
				# really shouldn't happen.
				new2old[idx] = lowerbound + 1

	# for new, old in enumerate(new2old):
	# 	print(str(new) + "  --  " + str(old))

	newmapfile = realign_map(maplines, new2old)

	with open(mapoutput + mapname, mode = "w", encoding = "utf-8") as f:
		for line in newmapfile:
			f.write(line)


if __name__ == "__main__":
	main()










