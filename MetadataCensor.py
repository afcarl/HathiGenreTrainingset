# Uses metadata to help assess degrees

import os, sys
import SonicScrewdriver as utils

rowindices, columns, metadata = utils.readtsv("/Users/tunder/Dropbox/PythonScripts/hathimeta/ExtractedMetadata.tsv")

modelindices, modelcolumns, modeldata = utils.readtsv("/Users/tunder/Dropbox/PythonScripts/hathimeta/newgenretable.txt")

options = ["non", "bio", "poe", "dra", "fic"]

def censor(htid, genresequence):

	htid = utils.pairtreelabel(htid)
	# convert the htid into a dirty pairtree label for metadata matching

	# Create a dictionary with entries for all possible conditions, initially set negative.
	symptoms = ["weakconfirmation", "weakdenial", "strongconfirmation", "strongdenial", "modelagrees", "modeldisagrees"]
	reported = dict()
	for symptom in symptoms:
		reported[symptom] = 0

	couldbefiction = True

	# Now we need to assess the largest genre in this volume.
	genrecounts = dict()
	genrecounts['fic'] = 0
	genrecounts['poe'] = 0
	genrecounts['dra'] = 0
	genrecounts['non'] = 0

	for page in genresequence:
		indexas = page

		# For this purpose, we treat biography and indexes as equivalent to nonfiction.
		if page == "bio" or page == "index" or page == "back":
			indexas = "non"

		utils.addtodict(indexas, 1, genrecounts)

	# Convert the dictionary of counts into a sorted list, and take the max.
	genretuples = utils.sortkeysbyvalue(genrecounts, whethertoreverse = True)
	maxgenre = genretuples[0][1]

	if htid not in rowindices and htid not in modelindices:
		return genresequence, reported

	if htid in rowindices:

		genrestring = metadata["genres"][htid]
		genreinfo = genrestring.split(";")
		# It's a semicolon-delimited list of items.

		for info in genreinfo:

			if info == "biog?" and maxgenre == "non":
				reported["weakconfirmation"] = 1
			if info == "biog?" and maxgenre != "non":
				reported["weakdenial"] = 1

			if info == "Not fiction" and maxgenre == "non":
				reported["weakconfirmation"] = 1
			if info == "Not fiction" and maxgenre == "fic":
				reported["weakdenial"] = 1

			if (info == "Fiction" or info == "Novel") and maxgenre == "fic":
				reported["strongconfirmation"] = 1
			if (info == "Fiction" or info == "Novel") and maxgenre != "fic":
				reported["strongdenial"] = 1

			if info == "Biography" and maxgenre == "non":
				reported["strongconfirmation"] = 1
				couldbefiction = False
			if info == "Biography" and maxgenre != "non":
				reported["strongdenial"] = 1

			if info == "Autobiography" and maxgenre == "non":
				reported["strongconfirmation"] = 1
				couldbefiction = False
			if info == "Autobiography" and maxgenre != "non":
				reported["strongdenial"] = 1

			if (info == "Poetry" or info == "Poems") and maxgenre == "poe":
				reported["strongconfirmation"] = 1
			if (info == "Poetry" or info == "Poems") and maxgenre != "poe":
				reported["strongdenial"] = 1

			if (info == "Drama" or info == "Tragedies" or info == "Comedies") and maxgenre == "dra":
				reported["strongconfirmation"] = 1
			if (info == "Drama" or info == "Tragedies" or info == "Comedies") and maxgenre != "dra":
				reported["strongdenial"] = 1

			if (info == "Catalog" or info == "Dictionary" or info=="Bibliographies") and maxgenre == "non":
				reported["strongconfirmation"] = 1
				couldbefiction = False
			if (info == "Catalog" or info == "Dictionary" or info=="Bibliographies") and maxgenre != "non":
				reported["strongdenial"] = 1
	else:
		print("Skipped.")

	if htid in modelindices:

		modelpredictions = dict()
		for genre, genrecolumn in modeldata.items():
			if not genre in options:
				# this column is not a genre!
				continue
			modelpredictions[genre] = float(genrecolumn[htid])
		predictionlist = utils.sortkeysbyvalue(modelpredictions, whethertoreverse = True)
		modelprediction = predictionlist[0][1]
		modelconfidence = predictionlist[0][0]
		nextclosest = predictionlist[1][0]
		# Take the top prediction.

		# For purposes of this routine, treat biography as nonfiction:
		if modelprediction == "bio":
			modelprediction = "non"

		if maxgenre == modelprediction:
			reported["modelagrees"] = 1 ## modelconfidence - nextclosest
			reported["modeldisagrees"] = 0
		if maxgenre != modelprediction:
			## divergence = modelconfidence - modelpredictions[maxgenre]
			reported["modeldisagrees"] = 1
			reported["modelagrees"] = 0
			## print(maxgenre + " ≠ " + modelprediction)
	else:
		reported["modelagrees"] = 0
		reported["modeldisagrees"] = 0


	if not couldbefiction and modelprediction == "non":
		
		numberofpages = len(genresequence)
		for i in range(numberofpages):
			if genresequence[i] == "fic":
				genresequence[i] = "non"

	return genresequence, reported


