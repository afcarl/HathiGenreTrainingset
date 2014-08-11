# Check two sets of pages for alignment.
# Ensemble.py

import os
import numpy as np
import shutil
import random

firstfolder = "/Users/tunder/Dropbox/pagedata/production/oldfiles/"
firstfiles = os.listdir(firstfolder)

validfiles = [x for x in firstfiles if not x.startswith(".")]

secondfolder = "/Users/tunder/Dropbox/pagedata/thirdfeatures/pagefeatures/"
secondfiles = set(os.listdir(secondfolder))

missing = [x for x in validfiles if x not in secondfiles]

if len(missing) > 0:
	print("Error -- missing files.")
	sys.exit()

def makesequence(fl1):
	pagedict = dict()
	pagesequence = list()
	oldpage = 0

	for line in fl1:
		line = line.rstrip()
		fields = line.split('\t')
		page = int(fields[0])
		if page < 0:
			continue
		token = fields[1]

		count = int(fields[2])

		if token == "#stdev":
			count = 0

		if page == oldpage:
			pagedict[token] = count
		else:
			pagesequence.append(pagedict)
			oldpage = page
			pagedict = dict()
			pagedict[token] = count


	pagesequence.append(pagedict)

	return pagesequence

def npcossim(v1, v2):
	if (np.sqrt(np.dot(v1, v1)) * np.sqrt(np.dot(v2, v2))) == 0:
		return 0.5
	else:
		return np.dot(v1, v2) / (np.sqrt(np.dot(v1, v1)) * np.sqrt(np.dot(v2, v2)))

def cos_sim (A, B):
	''' Calculate cosine similarity of two vectors.'''

	vectorlen = len(A)
	assert len(B) == vectorlen

	dotproduct = float(0.0)
	A_sum = float(0.0)
	B_sum = float(0.0)

	for i in range(0, vectorlen):
		dotproduct += A[i] * B[i]
		A_sum += A[i] * A[i]
		B_sum += B[i] * B[i]

	A_magnitude = math.sqrt(A_sum)
	B_magnitude = math.sqrt(B_sum)

	return dotproduct / (A_magnitude * B_magnitude)

def dict_cosine(dict1, dict2):
	keys1 = set(dict1.keys())
	keys2 = set(dict2.keys())
	allkeys = list(keys1.union(keys2))
	K = len(allkeys)

	vector1 = np.zeros(K)
	vector2 = np.zeros(K)
	for idx, akey in enumerate(allkeys):
		if akey in dict1:
			vector1[idx] = dict1[akey]
		if akey in dict2:
			vector2[idx] = dict2[akey]

	return npcossim(vector1, vector2)

def dict_sum(dict1):
	total = 0
	for key, value in dict1.items():
		if key != "#lines":
			total += value
	return total

def feature2map(filename):
	if len(filename) < 5:
		return "error"
	else:
		return filename[:-7] + ".map"

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

	assert number + 1 == len(mapseq)

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

# MAIN

oldfeatureinput = "/Users/tunder/Dropbox/pagedata/thirdfeatures/pagefeatures/"
oldmapinput = "/Users/tunder/Dropbox/pagedata/thirdfeatures/genremaps/"

newfeatureinput = "/Users/tunder/Dropbox/pagedata/production/oldfiles/"

featureoutput = "/Users/tunder/Dropbox/pagedata/fourthfeatures/pagefeatures/"
mapoutput = "/Users/tunder/Dropbox/pagedata/fourthfeatures/genremaps/"

failurelist = list()

for filename in validfiles:
	firstpath = firstfolder + filename
	secondpath = secondfolder + filename

	with open(firstpath, encoding = "utf-8") as f1:
		fl1 = f1.readlines()

	with open(secondpath, encoding = "utf-8") as f2:
		fl2 = f2.readlines()

	seq1 = makesequence(fl1)
	seq2 = makesequence(fl2)

	print()
	print(filename, len(seq1), len(seq2))

	idx1 = 0
	failuresinvol = 0
	oldpagenums = list()
	# The indexes of this list correspond to the new page numbers in seq1;
	# the numbers in those positions correspond to old page numbers in seq2.
	volsize = 0

	for idx2, page2 in enumerate(seq2):
		if idx1 < len(seq1):
			page1 = seq1[idx1]
		else:
			print("Overran the length of new sequence in " + filename)
			break

		dc = dict_cosine(page1, page2)
		print(dc)

		ds1 = dict_sum(page1)
		ds2 = dict_sum(page2)
		volsize += ds2

		if dc > 0.6 or (ds1 < 2 and ds2 < 2):
			oldpagenums.append(idx2)
			idx1 += 1

		else:
			succeed = False
			print("Pagelen: " + str(dict_sum(page1)))

			for offset in range(1, 8):
				# We don't want to skip forward beyond the end of seq1,
				# and in fact, we want to leave at least as many pages
				# in seq1 as remain in seq2!

				if (idx1 + offset + 1) < (len(seq1) - (len(seq2) - idx2)):
					newpage = seq1[idx1 + offset]
					if dict_cosine(newpage, page2) > 0.6:
						idx1 += offset
						idx1 += 1
						succeed = True
						print("Off " + str(offset) + " newlen " + str(ds1) + " oldlen " + str(ds2))
						for i in range(offset + 1):
							oldpagenums.append(idx2)
							# We are saying that more than one page in seq1 corresponds to
							# this page in the older seq2; there was an insertion.
						break

			if succeed == False:
				print("Could not align.")
				print(ds2)
				idx1 += 1
				failuresinvol += ds2
				failuresinvol += ds1
				oldpagenums.append(idx2)
				# In this case we continue by incrementing both indexes even though we
				# couldn't find a good match for the old page in the new sequence.

	if idx1 == len(seq1):
		print("WORKED with " + str(failuresinvol) + " failures.")

	else:

		for i in range(idx1, len(seq1)):

			print("Extra end page.")
			failuresinvol += dict_sum(seq1[i])
			oldpagenums.append(idx2)

		print("WORKED with " + str(failuresinvol) + " failures.")

	lengthsequal = (len(oldpagenums) == len(seq1))

	mapname = feature2map(filename)
	if len(seq1) == len(seq2):
		# If page lengths are the same, we can simply accept features based on
		# the new text.

		shutil.copyfile(newfeatureinput + filename, featureoutput + filename)
		shutil.copyfile(oldmapinput + mapname, mapoutput + mapname)

	elif lengthsequal and (failuresinvol/volsize * 100) < 0.2:
		# We conclude that old and new feature files can be aligned reasonably
		# reliably (failures involve less than 00.1% of words in the volume).
		# This means we can again accept the new features.

		shutil.copyfile(newfeatureinput + filename, featureoutput + filename)

		# In this case we need to transform the map file to correspond to the
		# new alignment.

		with open(oldmapinput + mapname, encoding = "utf-8") as f:
			maplines = f.readlines()

		newmapfile = realign_map(maplines, oldpagenums)

		with open(mapoutput + mapname, mode = "w", encoding = "utf-8") as f:
			for line in newmapfile:
				f.write(line)

	else:
		# For one reason or another, we don't trust the new alignment.
		# Stick with the old features.

		shutil.copyfile(oldfeatureinput + filename, featureoutput + filename)
		shutil.copyfile(oldmapinput + mapname, mapoutput + mapname)


	failurelist.append((failuresinvol/volsize) * 100)





