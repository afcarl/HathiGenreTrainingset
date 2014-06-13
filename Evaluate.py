# Evaluate page predictions
# EvaluatePagePredicts.py

import os
import numpy as np
import pandas as pd
from scipy.stats.stats import pearsonr
import SonicScrewdriver as utils
import MetadataCensor
import Coalescer
from math import log
import statsmodels.api as sm


def pairtreelabel(htid):
    ''' Given a clean htid, returns a dirty one that will match
    the metadata table.'''
    
    if '+' in htid or '=' in htid:
        htid = htid.replace('+',':')
        htid = htid.replace('=','/')

    return htid  

genretranslations = {'subsc' : 'front', 'argum': 'non', 'pref': 'non', 'aut': 'bio', 'bio': 'bio',
'toc': 'front', 'title': 'front', 'bookp': 'front',
'bibli': 'back', 'gloss': 'back', 'epi': 'fic', 'errat': 'non', 'notes': 'non', 'ora': 'non', 
'let': 'non', 'trv': 'non', 'lyr': 'poe', 'nar': 'poe', 'vdr': 'dra', 'pdr': 'dra',
'clo': 'dra', 'impri': 'front', 'libra': 'back', 'index': 'back'}

user = input("Which directory of predictions (genremaps or crossvalidate)? ")

predictdir = "/Volumes/TARDIS/output/" + user

groundtruthdir = "/Users/tunder/Dropbox/pagedata/" + user + "/genremaps/" 

groundtruthfiles = os.listdir(groundtruthdir)
predictfiles = os.listdir(predictdir)

# The base list here is produced by predictfiles
# because obvs we don't care about ground truth
# that we can't map to a prediction.

# Our goal in the next loop is to produce such a mapping.

matchedfilenames = dict()

for filename in predictfiles:
	if ".predict" not in filename:
		continue
	
	htid = filename[0:-8]

	groundtruthversion = htid + ".map"

	if groundtruthversion not in groundtruthfiles:
		print("Missing " + htid)
	else:
		matchedfilenames[filename] = groundtruthversion

# We have identified filenames. Now define functions.

def compare_two_lists(truelist, predicted):
	global genretranslations
	assert(len(truelist) == len(predicted))

	errorsbygenre = dict()
	correctbygenre = dict()
	accurate = 0
	inaccurate = 0
	totaltruegenre = dict()

	for index, truegenre in enumerate(truelist):
		if truegenre in genretranslations:
			truegenre = genretranslations[truegenre]

		utils.addtodict(truegenre, 1, totaltruegenre)

		predictedgenre = predicted[index]

		if truegenre == predictedgenre or (truegenre == "bio" and predictedgenre == "non") or (truegenre == "non" and predictedgenre == "bio"):
			utils.addtodict(truegenre, 1, correctbygenre)
			accurate += 1
		else:
			utils.addtodict((truegenre, predictedgenre), 1, errorsbygenre)
			inaccurate += 1

	return totaltruegenre, correctbygenre, errorsbygenre, accurate, inaccurate

def add_dictionary(masterdict, dicttoadd):
	for key, value in dicttoadd.items():
		if key in masterdict:
			masterdict[key] += value
		else:
			masterdict[key] = value
	return masterdict

def evaluate_filelist(matchedfilenames, excludedhtidlist):
	global predictdir, groundtruthdir

	smoothederrors = dict()
	unsmoothederrors = dict()
	smoothedcorrect = dict()
	unsmoothedcorrect = dict()
	coalescederrors = dict()
	coalescedcorrect = dict()
	totalgt = dict()
	roughaccurate = 0
	roughnotaccurate = 0
	smoothaccurate = 0
	smoothnotaccurate = 0
	coalescedaccurate = 0
	coalescednotaccurate = 0

	# The correct dictionaries pair a genre code (in the original) to a number of times it was correctly
	# identified

	# The error dictionaries map a tuple of (correct code, error code) to a number of times it occurred.

	truesequences = dict()
	predictedsequences = dict()
	accuracies = dict()
	metadatatable = dict()

	symptoms = ["weakconfirmation", "weakdenial", "strongconfirmation", "strongdenial", "modelagrees", "modeldisagrees"]
	for symptom in symptoms:
		metadatatable[symptom] = dict()
	metadatatable["numberofchunks"] = dict()
	metadatatable["fictonon"] = dict()
	metadatatable["bio"] = dict()

	for pfile, gtfile in matchedfilenames.items():
		htid = gtfile[0:-4]
		if htid in excludedhtidlist:
			continue

		# The predictionfile has three columns, of which the second
		# is an unsmoothed prediction and the third is smoothed

		smoothlist = list()
		roughlist = list()

		pfilepath = os.path.join(predictdir, pfile)
		with open(pfilepath,encoding = "utf-8") as f:
			filelines = f.readlines()

		for line in filelines:
			line = line.rstrip()
			fields = line.split('\t')
			roughlist.append(fields[1])
			smoothlist.append(fields[2])

		correctlist = list()

		gtfilepath = os.path.join(groundtruthdir, gtfile)
		with open(gtfilepath,encoding = "utf-8") as f:
			filelines = f.readlines()

		for line in filelines:
			line = line.rstrip()
			fields = line.split('\t')
			correctlist.append(fields[1])

		assert len(correctlist) == len(roughlist)

		# Experiment.
		oldgenre = ""
		transitioncount = 0
		biocount = 0
		for agenre in roughlist:
			if agenre == "bio":
				biocount += 1
			if oldgenre == "fic" and (agenre == "non" or agenre =="bio"):
				transitioncount += 1
			oldgenre = agenre

		coalescedlist, numberofdistinctsequences = Coalescer.coalesce(smoothlist)
		
		coalescedlist, metadataconfirmation = MetadataCensor.censor(htid, coalescedlist)

		for key, value in metadataconfirmation.items():
			metadatatable[key][htid] = value
		metadatatable["numberofchunks"][htid] = log(numberofdistinctsequences + 1)
		metadatatable["fictonon"][htid] = transitioncount
		metadatatable["bio"][htid] = biocount / len(roughlist)
		# This is significant. We don't want to overpenalize long books, but there is
		# a correlation between the number of predicted genre shifts and inaccuracy.
		# So we take the log.

		totaltruegenre, correctbygenre, errorsbygenre, accurate, inaccurate = compare_two_lists(correctlist, smoothlist)
		add_dictionary(smoothederrors, errorsbygenre)
		add_dictionary(smoothedcorrect, correctbygenre)
		add_dictionary(totalgt, totaltruegenre)
		# Only do this for one comparison
		smoothaccurate += accurate
		smoothnotaccurate += inaccurate

		totaltruegenre, correctbygenre, errorsbygenre, accurate, inaccurate = compare_two_lists(correctlist, roughlist)
		add_dictionary(unsmoothederrors, errorsbygenre)
		add_dictionary(unsmoothedcorrect, correctbygenre)
		roughaccurate += accurate
		roughnotaccurate += inaccurate

		totaltruegenre, correctbygenre, errorsbygenre, accurate, inaccurate = compare_two_lists(correctlist, coalescedlist)
		add_dictionary(coalescederrors, errorsbygenre)
		add_dictionary(coalescedcorrect, correctbygenre)
		coalescedaccurate += accurate
		coalescednotaccurate += inaccurate

		truesequences[gtfile] = correctlist
		predictedsequences[gtfile] = coalescedlist
		thisaccuracy = accurate / (accurate + inaccurate)
		accuracies[htid] = thisaccuracy

	# Now we need to interpret the dictionaries.

	for genre, count in totalgt.items():

		print()
		print(genre.upper() + " : " + str(count))

		if count < 1:
			continue

		print()
		print("UNSMOOTHED PREDICTION, " + str(count) + " | " + genre)

		print("Correctly identified: " + str(unsmoothedcorrect.get(genre, 0) / count))
		print("Errors: ")

		for key, errorcount in unsmoothederrors.items():
			gt, predict = key
			if gt == genre:
				print(predict + ": " + str(errorcount) + "   " + str (errorcount/count))

		print()
		print("SMOOTHED PREDICTION, " + str(count) + " | " + genre)

		print("Correctly identified: " + str(smoothedcorrect.get(genre, 0) / count))
		print("Errors: ")

		for key, errorcount in smoothederrors.items():
			gt, smoothed = key
			if gt == genre:
				print(smoothed + ": " + str(errorcount) + "   " + str (errorcount/count))

	roughaccuracy = roughaccurate / (roughaccurate + roughnotaccurate)
	smoothaccuracy = smoothaccurate / (smoothaccurate + smoothnotaccurate)
	coalaccuracy = coalescedaccurate / (coalescedaccurate + coalescednotaccurate)

	return metadatatable, accuracies, roughaccuracy, smoothaccuracy, coalaccuracy

metadatatable, accuracies, roughaccuracy, smoothaccuracy, coalaccuracy = evaluate_filelist(matchedfilenames, list())

print()
print("ROUGH MICROACCURACY:")
print(roughaccuracy)
print("SMOOTHED MICROACCURACY:")
print(smoothaccuracy)
print("COALESCED MICROACCURACY:")
print(coalaccuracy)

metadatapath = os.path.join(predictdir, "predictionMetadata.tsv")
rowindices, columns, metadata = utils.readtsv(metadatapath)

metadatatable['maxprob']= metadata['maxprob']
metadatatable['gap'] = metadata['gap']
metadatatable['accuracy'] = accuracies

data = pd.DataFrame(metadatatable, dtype = "float") 

data['intercept'] = 1.0
train_cols = data.columns[1:]
logit = sm.Logit(data['accuracy'], data[train_cols])
result = logit.fit()
print(result.summary())
predictions = result.predict(data[train_cols])
print(pearsonr(data['accuracy'], predictions))

user = input("Continue? ")

idstoexclude = [x for x in data.index[predictions < .9]]

metadatatable, newaccuracies, roughaccuracy, smoothaccuracy, coalaccuracy = evaluate_filelist(matchedfilenames, idstoexclude)

print()
print("ROUGH MICROACCURACY:")
print(roughaccuracy)
print("SMOOTHED MICROACCURACY:")
print(smoothaccuracy)
print("COALESCED MICROACCURACY:")
print(coalaccuracy)

user = input("Continue? ")

for filename, accuracy in accuracies.items():
	
	print(accuracy, filename)

	truesequence = truesequences[filename]
	predictedsequence = predictedsequences[filename]

	for index, truegenre in enumerate(truesequence):
		print(truegenre + ' \t ' + predictedsequence[index])

	user = input("Continue? ")









