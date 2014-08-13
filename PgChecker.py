# Check two sets of pages for agreement.

import os
import glob

def makedict(fl1):
	totaldict = dict()

	for line in fl1:
		line = line.rstrip()
		fields = line.split('\t')
		page = int(fields[0])
		token = fields[1]
		count = int(fields[2])

		if token in totaldict:
			totaldict[token] += count
		else:
			totaldict[token] = count

	return totaldict

def makesequence(fl1):
	pagedict = dict()
	pagesequence = list()
	oldpage = -1

	for line in fl1:
		line = line.rstrip()
		fields = line.split('\t')
		page = int(fields[0])
		token = fields[1]
		count = int(fields[2])

		if page == oldpage:
			pagedict[token] = count
		else:
			pagesequence.append(pagedict)
			oldpage = page

	pagesequence.append(pagedict)

	return pagesequence

# def comparethetwo(fl1, fl2):

# 	seq1 = makesequence(fl1)
# 	seq2 = makesequence(fl2)

# 	idx = 0

# 	for pagedict in seq1:
# 		pagedict2 = seq2[idx]

# 		if len(pagedict) == len(pagedict2):
# 			comparepage(pagedict, pagedict2)
# 		elif len(pagedict) < 2:
# 			continue

# 		idx += 1

def comparethetwo(fl1, fl2):

	d1 = makedict(fl1)
	d2 = makedict(fl2)

	comparepage(d1, d2)

def comparepage(dict1, dict2):
	for key, value in dict1.items():
		if key in dict2:
			value2 = dict2[key]
		else:
			value2 = 0

		if (value - value2) != 0:
			print(key + " " + str(value - value2))

def pairtreelabel(htid):
    ''' Given a clean htid, returns a dirty one that will match
    the metadata table.'''

    if '+' in htid or '=' in htid:
        htid = htid.replace('+',':')
        htid = htid.replace('=','/')

    return htid

firstfolder = "/Users/tunder/Dropbox/pagedata/production/oldfiles/"
firstfiles = os.listdir(firstfolder)

validfiles = [x for x in firstfiles if not x.startswith(".")]

secondfolder = "/Users/tunder/Dropbox/pagedata/thirdfeatures/pagefeatures/"

for filename in validfiles:
	firstpath = firstfolder + filename
	with open(firstpath, encoding = "utf-8") as f:
		fl1 = f.readlines()
	secondpath = secondfolder + filename
	try:
		with open(secondpath, encoding = "utf-8") as f:
			fl2 = f.readlines()
		print()
		print("Found " + filename)

		comparethetwo(fl1, fl2)

	except:
		pass



