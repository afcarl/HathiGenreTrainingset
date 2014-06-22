# This is based on Evaluate.py, but stripped down because
# we don't have any ground truth to compare. We aren't evaluating
# model performance; we're just predicting the accuracy of our
# predictions on unknown volumes.

import os
import numpy as np
import pandas as pd
from scipy.stats.stats import pearsonr
import SonicScrewdriver as utils
import MetadataCascades
import Coalescer
from math import log
import statsmodels.api as sm
import pickle

def pairtreelabel(htid):
    ''' Given a clean htid, returns a dirty one that will match
    the metadata table.'''

    if '+' in htid or '=' in htid:
        htid = htid.replace('+',':')
        htid = htid.replace('=','/')

    return htid

genretranslations = {'subsc' : 'front', 'argum': 'non', 'pref': 'non', 'aut': 'bio', 'bio': 'bio', 'toc': 'front', 'title': 'front', 'bookp': 'front', 'bibli': 'back', 'gloss': 'back', 'epi': 'fic', 'errat': 'non', 'notes': 'non', 'ora': 'non', 'let': 'non', 'trv': 'non', 'lyr': 'poe', 'nar': 'poe', 'vdr': 'dra', 'pdr': 'dra', 'clo': 'dra', 'impri': 'front', 'libra': 'back', 'index': 'back'}

predictdir = input("Directory to assess? ")

predictfiles = os.listdir(predictdir)

def add_dictionary(masterdict, dicttoadd):
	for key, value in dicttoadd.items():
		if key in masterdict:
			masterdict[key] += value
		else:
			masterdict[key] = value
	return masterdict


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

counter = 0
for afile in predictfiles:
	if afile.startswith(".") or afile.startswith("_") or afile.startswith("prediction"):
		continue

	counter += 1
	if counter % 10 == 1:
		print(counter)

	htid = afile[:-8]

	# The predictionfile has three columns, of which the second
	# is an unsmoothed prediction and the third is smoothed

	smoothlist = list()
	roughlist = list()

	pfilepath = os.path.join(predictdir, afile)
	with open(pfilepath,encoding = "utf-8") as f:
		filelines = f.readlines()

	for line in filelines:
		line = line.rstrip()
		fields = line.split('\t')
		roughlist.append(fields[1])
		smoothlist.append(fields[2])

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

	metadataconfirmation = MetadataCascades.metadata_check(htid, coalescedlist)

	for key, value in metadataconfirmation.items():
		metadatatable[key][htid] = value
	metadatatable["numberofchunks"][htid] = log(numberofdistinctsequences + 1)
	metadatatable["fictonon"][htid] = transitioncount
	metadatatable["bio"][htid] = biocount / len(roughlist)
	# This is significant. We don't want to overpenalize long books, but there is
	# a correlation between the number of predicted genre shifts and inaccuracy.
	# So we take the log.

# Now we need to interpret the dictionaries.

metadatapath = os.path.join(predictdir, "predictionMetadata.tsv")
rowindices, columns, metadata = utils.readtsv(metadatapath)

maxprob = dict()
for key, value in metadata['maxprob'].items():
	if value != "NA":
		maxprob[key] = float(value)

gap = dict()
for key, value in metadata['gap'].items():
	if value != "NA":
		gap[key] = float(value)


metadatatable['maxprob']= maxprob
metadatatable['gap'] = gap

data = pd.DataFrame(metadatatable, dtype = "float")
data['intercept'] = 1.0
data = data.dropna()

parameters = pd.Series.from_csv("/Volumes/TARDIS/output/models/ConfidenceModelParameters.csv")
from LogisticPredict import logitpredict
predictions = logitpredict(parameters, data)

# with open("/Volumes/TARDIS/output/models/results.txt", mode ="w") as f:
# 	for idx, prediction in enumerate(predictions):
# 		f.write(str(idx) + '\t' + data.index[idx] + '\t' + str(prediction) + '\n')

# This will also do it more easily:

# with open("/Volumes/TARDIS/output/models/PredictAccuracy.p", mode = "r+b") as f:
# 	model = pickle.load(f)

# otherpredictions = model.predict(data)

import SonicScrewdriver as utils

indices = [utils.pairtreelabel(x) for x in data.index]

decorated = [x for x in zip(predictions, indices)]
decorated.sort()
sortedpredictions, sortedindices = zip(*decorated)

with open("/Users/tunder/Dropbox/PythonScripts/hathimeta/ExtractedMetadata.tsv", mode = "r", encoding = "utf-8") as f:
	filelines = f.readlines()

linedict=dict()
for line in filelines[1:]:
	line = line.rstrip()
	fields = line.split('\t')
	headlessline = '\t'.join(fields[1:])
	linedict[fields[0]] = headlessline

header = filelines[0].rstrip()
headerfields = header.split('\t')
newheading = headerfields[0] + '\t' + "accuracy" + "\t" + "\t".join(headerfields[1:]) + "\n"

with open("/Users/tunder/Dropbox/pagedata/interrater/MachineConfidence.tsv", mode="w", encoding="utf-8") as f:
	f.write(newheading)
	# heading
	for idx in range(len(sortedindices)):
		f.write(sortedindices[idx] + '\t' + str(sortedpredictions[idx]) + '\t' + linedict[sortedindices[idx]] + '\n')









