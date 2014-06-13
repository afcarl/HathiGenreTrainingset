# MakeSampleData

import json
import SonicScrewdriver as utils

topvolumes = dict()
topwords = dict()

for i in range (1700, 1900):
	topvolumes[i] = {"nonfiction": 0, "poetry": 0, "drama": 0, "fiction": 0, "mixed": 0}
	topwords[i] = {"nonfiction": 0, "poetry": 0, "drama": 0, "fiction": 0, "paratext": 0}

options = ["non", "bio", "poe", "dra", "fic"]
translations = {"non": "nonfiction", "poe": "poetry", "dra": "drama", "fic": "fiction"}
translated = ["nonfiction", "poetry", "drama", "fiction"]

modelindices, modelcolumns, modeldata = utils.readtsv("/Users/tunder/Dropbox/PythonScripts/hathimeta/newgenretable.txt")
indices, columns, metadata = utils.readtsv("/Users/tunder/Dropbox/PythonScripts/hathimeta/ExtractedMetadata.tsv")

for row in modelindices:
	modelwords = dict()
	for genre in translated:
		modelwords[genre] = 0

	for genre, genrecolumn in modeldata.items():
		if not genre in options:
			# this column is not a genre!
			continue
		thesewords = round(float(genrecolumn[row]) * 50000)
		if genre == "bio":
			modelwords["nonfiction"] += thesewords
		else:
			key = translations[genre]
			modelwords[key] += thesewords
		modelwords["paratext"] = 1000

	modelpredictions = dict()
	for genre, genrecolumn in modeldata.items():
		if not genre in options:
			# this column is not a genre!
			continue
		modelpredictions[genre] = float(genrecolumn[row])
	predictionlist = utils.sortkeysbyvalue(modelpredictions, whethertoreverse = True)
	modelprediction = predictionlist[0][1]
	# Take the top prediction.

	# For purposes of this routine, treat biography as nonfiction:
	if modelprediction == "bio":
		modelprediction = "non"
	volgenrekey = translations[modelprediction]

	date = metadata["date"][row]
	try:
		integerdate = int(date)
	except:
		integerdate = 0

	if integerdate > 1699 and integerdate < 1900:
		topvolumes[integerdate][volgenrekey] += 1

		for key, value in modelwords.items():
			topwords[integerdate][key] += value

for i in range(1700,1899):
	topvolumes[i]["mixed"] = round(topvolumes[i]["poetry"] / 2)

volumesubgraphs = {"nonfiction": dict(), "poetry": dict(), "drama": dict(), "fiction": dict(), "mixed": dict()}
wordsubgraphs = {"nonfiction": dict(), "fiction": dict(), "poetry": dict(), "drama": dict(), "paratext": dict()}

for key, value in volumesubgraphs.items():
	for i in range(1700,1900):
		value[i] = dict()

for key, value in wordsubgraphs.items():
	for i in range(1700,1900):
		value[i] = dict()

for year in range(1700,1900):
	non = topwords[year]["nonfiction"]
	bio = round(non * .12)
	auto = round(non * .03)
	para = round(non * .1)
	introductionquota = round(non * 0.05)
	non = non - (bio + auto + para + (introductionquota * 3))
	volumesubgraphs["nonfiction"][year]["unknown"] = non
	volumesubgraphs["nonfiction"][year]["biography"] = bio
	volumesubgraphs["nonfiction"][year]["autobiography"] = auto
	volumesubgraphs["nonfiction"][year]["paratext"] = para

	base = topwords[year]["fiction"]
	first = round(base * .12)
	third = round(base * .03)
	epist = round(base * .1)
	para = round(base * .1)
	base = base - (first + third + epist + para)
	volumesubgraphs["fiction"][year]["unknown"] = base
	volumesubgraphs["fiction"][year]["first-person"] = first
	volumesubgraphs["fiction"][year]["third-person"] = third
	volumesubgraphs["fiction"][year]["epistolary"] = epist
	volumesubgraphs["fiction"][year]["paratext"] = para
	volumesubgraphs["fiction"][year]["nonfiction"] = introductionquota

	base = topwords[year]["drama"]
	comedy = round(base * .20)
	tragedy = round(base * .30)
	para = round(base * .1)
	base = base - (comedy + tragedy + para)
	volumesubgraphs["drama"][year]["unknown"] = base
	volumesubgraphs["drama"][year]["comedy"] = comedy
	volumesubgraphs["drama"][year]["tragedy"] = tragedy
	volumesubgraphs["drama"][year]["paratext"] = para
	volumesubgraphs["drama"][year]["nonfiction"] = introductionquota

	base = topwords[year]["poetry"]
	para = round(base * .1)
	base = base - para
	volumesubgraphs["poetry"][year]["unknown"] = base
	volumesubgraphs["poetry"][year]["paratext"] = para
	volumesubgraphs["poetry"][year]["nonfiction"] = introductionquota

	volumesubgraphs["mixed"][year]["poetry"] = round(volumesubgraphs["poetry"][year]["unknown"] / 2)
	volumesubgraphs["mixed"][year]["drama"] = round(volumesubgraphs["drama"][year]["unknown"] / 2)
	volumesubgraphs["mixed"][year]["fiction"] = round(volumesubgraphs["fiction"][year]["unknown"] / 2)
	volumesubgraphs["mixed"][year]["nonfiction"] = round(volumesubgraphs["nonfiction"][year]["biography"] / 2)
	volumesubgraphs["mixed"][year]["paratext"] = round(volumesubgraphs["nonfiction"][year]["paratext"] / 2)


for i in range(1700,1900):
	wordsubgraphs["paratext"][i] = {"front matter": 0, "back matter": 0, "advertisements": 0, "unknown": 0}
	wordsubgraphs["fiction"][i] = {"unknown": 0, "first-person": 0, "third-person": 0, "epistolary": 0}
	wordsubgraphs["nonfiction"][i] = {"unknown": 0, "biography": 0, "autobiography": 0, "introductions": 0}
	wordsubgraphs["drama"][i] = {"comedy": 0, "tragedy": 0, "unknown": 0}
	wordsubgraphs["poetry"][i] = {"unknown": 0}


for genre in volumesubgraphs.keys():
	if genre == "mixed":
		for i in range(1700, 1900):
			for subgenre, value in volumesubgraphs[genre][i].items():
				wordsubgraphs[subgenre][i]["unknown"] += value
	else:
		for i in range(1700, 1900):
			for subgenre, value in volumesubgraphs[genre][i].items():
				if subgenre != "paratext" and subgenre != "nonfiction":
					wordsubgraphs[genre][i][subgenre] = value
				elif subgenre == "paratext":
					front = round(value * .2)
					back = round(value * .35)
					ads = round(value * .15)
					base = value - (front + back + ads)
					wordsubgraphs["paratext"][i]["front matter"] += front
					wordsubgraphs["paratext"][i]["back matter"] += back
					wordsubgraphs["paratext"][i]["advertisements"] += ads
					wordsubgraphs["paratext"][i]["unknown"] += base
				elif subgenre == "nonfiction":
					wordsubgraphs["nonfiction"][i]["introductions"] += value


jsondict = {"top-level volume graph": topvolumes, "top-level word graph": topwords, 
"subgraphs for volumes": volumesubgraphs, "subgraphs for words": wordsubgraphs}

jsonobject = json.dumps(jsondict)

with open("/Users/tunder/Dropbox/pagedata/sampledata.json", mode="w", encoding = "utf-8") as f:
	f.write(jsonobject)










