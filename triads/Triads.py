# Triads.py
#
# A semi-principled approach to smoothing sequences of page predictions that were
# produced by an ensemble of classifiers. Note that we've already applied a
# more strictly principled hidden Markov model to these sequences; we're now
# dealing with longer-range dependencies in the sequence, using a discriminative
# strategy.
#
# The general approach is to divide the sequence into "chunks" of generically
# identical pages, and then consider "triads" of chunks. I.e., chunks A-1, A, and A+1
# will constitute a "triad." We then consider the possibility that A should be
# assimilated to A-1 or A+1, using a wide range of predictors. For instance, since
# these predictions come from an ensemble, we know how *confident* the ensemble was
# about each chunk. If A is a) brief b) an uncertain prediction and c) surrounded by
# long sequences of confident predictions, and especially if d) A-1 and A+1 belong
# to the *same* genre, we're going to be pretty convinced that A should be smoothed
# out.
#
# However, there are a lot of predictors and the rules vary by genre. So
# instead of making ad hoc rules, we attempt to train a model on triads, using
# ground truth to discover the probabilities associated with particular combinations
# of predictors. We cross-validate this, obviously.
#
# Then we apply the model to out-of-sample volumes, in order to predict chunks
# that need smoothing. Because this is in many respects a tipping-point problem,
# we don't simply apply the model once to all triads. Instead we predict the
# triad most likely to need changing, change it, and then recalculate the
# probabilities for all triads in the new sequence. We repeat this until there
# are no triads above a threshold probability of wrongness.

import numpy as np
import SonicScrewdriver as utils
import EnsembleModule
import Triadifier

from sklearn.ensemble import RandomForestClassifier

def are_equal(genrea, genreb):
	'''We're not collapsing non and bio in this process, but we do treat them
	as equal when we're deciding whether to give the model a clue about the
	similarity of two segments.'''

	equivalent = {"non", "bio"}

	if genrea == genreb:
		return True
	elif genrea in equivalent and genreb in equivalent:
		return True
	else:
		return False

def nexthighest(dictionary):
	'''Returns the key with next-to-highest value in the
	dictionary provided. Assumes numeric values and string
	keys.'''

	maxval = 0
	nextval = 0
	maxkey = ""
	nextkey = ""
	for key, value in dictionary.items():
		if value > maxval:
			nextval = maxval
			maxval = value
			nextkey = maxkey
			maxkey = key
		elif value > nextval:
			nextval = value
			nextkey = key

	return nextkey

def sequence_to_counts(genresequence):
	'''Converts a sequence of page-level predictions to
	a dictionary of counts reflecting the number of pages
	assigned to each genre.

	Note that this version of the function is slightly different
	from the version in MetadataCascades, in allowing a wider range
	of genres and not initializing anything to zero.'''

	genrecounts = dict()

	for page in genresequence:
		utils.addtodict(page, 1, genrecounts)

	return genrecounts

def normalize_dict(dictionary):
	'''Normalizes the values of a dictionary by
	dividing by the total of all values.'''

	totalsum = 0
	keyset = list()
	for key, value in dictionary.items():
		totalsum += value
		keyset.append(key)

	newdictionary = dict()
	for key in keyset:
		newdictionary[key] = dictionary[key] / totalsum

	return newdictionary

# BEGIN MAIN.

genrelist = ["begin", "end", "ads", "bio", "dra", "fic", "poe", "non", "front", "back"]

def genrevectorizer(genre):
	global genrelist

	''' Converts a single nominal feature into a vectorized array of ten
	numeric features, all of which will be zero except for the 1 corresponding
	to the actual genre.'''

	vectorized = np.zeros(10)

	if genre in genrelist:
		idx = genrelist.index(genre)
	else:
		print("Error: Genre " + genre + " not found in genrevectorizer.")
		idx = 0

	vectorized[idx] = 1
	return vectorized

consensus, secondthoughts, pageprobsforfile, dissentsequences, groundtruths = EnsembleModule.main()

assert len(consensus) == len(groundtruths)
assert len(secondthoughts) == len(dissentsequences)
assert len(consensus) == len(secondthoughts)
# Basically, all of the dictionaries we just loaded need to have a key-value
# for every htid.

volumeset = [x for x in consensus.keys()]

# We need to divide the volumes into FOLDNUM subsets for crossvalidation.

folds = dict()
FOLDNUM = 5

for fold in range(FOLDNUM):
	folds[fold] = list()

for idx, htid in enumerate(volumeset):
	remainder = idx % FOLDNUM
	folds[remainder].append(htid)

# Now we proceed to crossvalidation:

for fold in range(FOLDNUM):
	print()
	print("Fold " + str(fold))

	testids = folds[fold]
	trainingids = list()
	for i in range(FOLDNUM):
		if i != fold:
			trainingids.extend(folds[i])

	# For each ID in trainingIDs, we need to generate a set of triads.

	trainingfeatures = list()
	trainingclasses = list()

	for htid in trainingids:
		predictedgenres = consensus[htid]
		runnersup = secondthoughts[htid]
		pageprobs = pageprobsforfile[htid]
		dissentseq = dissentsequences[htid]
		groundtruth = groundtruths[htid]

		volfeatures, volclasses = Triadifier.gettriads(predictedgenres, runnersup, pageprobs, dissentseq, groundtruth)
		trainingfeatures.extend(volfeatures)
		trainingclasses.extend(volclasses)

	# We grow features and classes as ordinary Python lists, because those are dynamic
	# and easily extensible. Then we convert to numpy.

	trainingfeatures = np.array(trainingfeatures, dtype= "float64")
	trainingclasses = np.array(trainingclasses, dtype= "int64")

	print("Features generated. Now training model.")

	forest = RandomForestClassifier(n_estimators = 100)
	forest = forest.fit(trainingfeatures, trainingclasses)

	testfeatures = list()
	testclasses = list()

	for htid in testids:
		predictedgenres = consensus[htid]
		runnersup = secondthoughts[htid]
		pageprobs = pageprobsforfile[htid]
		dissentseq = dissentsequences[htid]
		groundtruth = groundtruths[htid]

		volfeatures, volclasses = Triadifier.gettriads(predictedgenres, runnersup, pageprobs, dissentseq, groundtruth)
		testfeatures.extend(volfeatures)
		testclasses.extend(volclasses)

	testfeatures = np.array(testfeatures, dtype= "float64")
	testclasses = np.array(testclasses, dtype= "int64")

	predictions = forest.predict(testfeatures)

	truepredictions = 0
	for idx, prediction in enumerate(predictions):
		if prediction == testclasses[idx]:
			truepredictions += 1

	accuracy = truepredictions / len(predictions)
	print()
	print("Accuracy for fold " + str(fold) + " = " + str(accuracy))
	print()

print("Done.\a")

