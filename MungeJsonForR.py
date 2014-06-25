# MungeJsonForR

import json

smooth = True

with open("/Users/tunder/Dropbox/pagedata/jsons/realdata.json", mode="r", encoding = "utf-8") as f:
	jsonstring = f.read()

jsonobject = json.loads(jsonstring)

word = jsonobject["top_level_word_graph"]

options = ["poetry", "nonfiction", "drama", "fiction", "paratext"]

if smooth:
	for option in options:
		smoothed = list()
		for i in range(200):
			start = i - 1
			if start < 0:
				start = 0
			end = i + 1
			if end > 199:
				end = 199
			smoothed.append((word[option][start]+word[option][i]+word[option][end]) / 3.0)

		word[option] = smoothed

def sumall(jobj, options):
	totallist = list()
	for i in range(200):
		total = 0
		for option in options:
			total += jobj[option][i]
		totallist.append(total)
	return totallist

totallist = sumall(word, options)

def normalize(jobj, options, totals):
	newobject = dict()
	for option in options:
		normalizedversion = list()
		for i in range(200):
			oldvalue = jobj[option][i]
			newvalue = oldvalue / totals[i]
			normalizedversion.append(newvalue)
		newobject[option] = normalizedversion
	return newobject

normalized = normalize(word, options, totallist)

with open("/Users/tunder/Dropbox/pagedata/jsons/forR2.tsv", mode="w", encoding = "utf-8") as f:
	outline = "date\tpoetry\tnonfiction\tdrama\tfiction\tparatext\n"
	f.write(outline)
	for i in range(200):
		date = 1700 + i
		outline = str(date)
		for option in options:
			outline = outline + "\t" + str(normalized[option][i])
		f.write(outline + "\n")

