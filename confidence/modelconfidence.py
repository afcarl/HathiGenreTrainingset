# modelconfidence.py

# Uses internal evidence in page-level predictions, plus metadata, to produce
# a model of accuracy for these predictions.

import json
import os, sys
import numpy as np
import pandas as pd
import SonicScrewdriver as utils
from sklearn.linear_model import LogisticRegression
from sklearn import cross_validation
from scipy.stats.stats import pearsonr

genretranslations = {'subsc' : 'front', 'argum': 'non', 'pref': 'non', 'aut': 'bio', 'bio': 'bio', 'toc': 'front', 'title': 'front', 'bookp': 'front', 'bibli': 'ads', 'gloss': 'back', 'epi': 'fic', 'errat': 'non', 'notes': 'non', 'ora': 'non', 'let': 'bio', 'trv': 'non', 'lyr': 'poe', 'nar': 'poe', 'vdr': 'dra', 'pdr': 'dra', 'clo': 'dra', 'impri': 'front', 'libra': 'back', 'index': 'back'}

def sequence_to_counts(genresequence):
    '''Converts a sequence of page-level predictions to
    a dictionary of counts reflecting the number of pages
    assigned to each genre. Also reports the largest genre.
    Note that this function cannot return "bio." If
    biography is the largest genre it returns "non"fiction.
    It counts bio, but ensures that all votes for bio are also votes
    for non.
    '''

    genrecounts = dict()

    for page in genresequence:
        utils.addtodict(page, 1, genrecounts)
        if page == 'bio':
            utils.addtodict('non', 1, genrecounts)

    # Convert the dictionary of counts into a sorted list, and take the max.
    genretuples = utils.sortkeysbyvalue(genrecounts, whethertoreverse = True)
    maxgenre = genretuples[0][1]

    if maxgenre == 'bio':
        maxgenre = 'non'

    return genrecounts, maxgenre

def count_flips(sequence):
    numflips = 0
    prevgenre = ""
    for genre in sequence:
        if genre != prevgenre:
            numflips += 1

        prevgenre = genre

    return numflips

class Prediction:

    def __init__(self, filepath):
        with open(filepath, encoding='utf-8') as f:
            filelines = f.readlines()
        jsonobject = json.loads(filelines[0])
        self.dirtyid = jsonobject['volID']
        self.rawPredictions = jsonobject['rawPredictions']
        self.smoothPredictions = jsonobject['smoothedPredictions']
        self.probabilities = jsonobject['smoothedProbabilities']
        self.avggap = jsonobject['avgGap']
        self.maxprob = jsonobject['avgMaxProb']
        self.pagelen = len(self.smoothPredictions)

        genrecounts, self.maxgenre = sequence_to_counts(self.smoothPredictions)
        pagesinmax = genrecounts[self.maxgenre]
        self.maxratio = pagesinmax / self.pagelen

        self.rawflipratio = (count_flips(self.rawPredictions) / self.pagelen)
        self.smoothflips = count_flips(self.smoothPredictions)

        if 'bio' in genrecounts and genrecounts['bio'] > (self.pagelen / 2):
            self.bioflag = True
        else:
            self.bioflag = False

    def addmetadata(self, row, table):
        self.author = table['author'][row]
        self.title = table['title'][row]
        self.date = utils.simple_date(row, table)
        genrelist = table['genres'][row].split(';')
        self.genres = set(genrelist)

        varietiesofnon = ['Bibliographies', 'Catalog', 'Dictionary', 'Encyclopedia', 'Handbooks', 'Indexes', 'Legislation', 'Directories', 'Statistics', 'Legal cases', 'Legal articles', 'Calendars', 'Autobiography', 'Biography', 'Letters', 'Essays', 'Speeches']

        self.nonmetaflag = False
        for genre in varietiesofnon:
            if genre in self.genres:
                self.nonmetaflag = True

    def missingmetadata(self):
        self.author = ''
        self.title = ''
        self.date = ''
        self.genres = set()
        self.nonmetaflag = False

    def getfeatures(self):

        features = np.zeros(13)

        if self.maxgenre == 'fic':

            if 'Fiction' in self.genres or 'Novel' in self.genres or 'Short stories' in self.genres:
                features[0] = 1

            if 'Drama' in self.genres or 'Poetry' in self.genres or self.nonmetaflag:
                features[1] = 1

        if self.maxgenre == 'poe':

            if 'Poetry' in self.genres or 'poems' in self.title.lower():
                features[2] = 1

            if 'Drama' in self.genres or 'Fiction' in self.genres or self.nonmetaflag:
                features[3] = 1

        if self.maxgenre == 'dra':
            if 'Drama' in self.genres or 'plays' in self.title.lower():
                features[4] = 1

            if 'Fiction' in self.genres or 'Poetry' in self.genres or self.nonmetaflag:
                features[5] = 1

        if self.maxgenre == 'non':

            if self.nonmetaflag:
                features[6] = 1

            if 'Fiction' in self.genres or 'Poetry' in self.genres or 'Drama' in self.genres or 'Novel' in self.genres or 'Short stories' in self.genres:
                features[7] = 1

        features[8] = self.maxratio
        features[9] = self.rawflipratio
        features[10] = self.smoothflips
        features[11] = self.avggap
        features[12] = self.maxprob

        return features

    def match(self, correctgenres):
        assert len(correctgenres) == len(self.smoothPredictions)
        matches = 0
        for idx, genre in enumerate(self.smoothPredictions):
            if correctgenres[idx] == genre:
                matches += 1
            elif correctgenres[idx] == 'bio' and genre == 'non':
                matches += 1
            elif correctgenres[idx] == 'non' and genre == 'bio':
                matches += 1

        return matches / self.pagelen


# Begin main script.

metadatapath = '/Volumes/TARDIS/work/metadata/MergedMonographs.tsv'
rows, columns, table = utils.readtsv(metadatapath)

firstsource = "/Users/tunder/Dropbox/pagedata/to1923features/genremaps/"
secondsource = "/Users/tunder/Dropbox/pagedata/seventhfeatures/genremaps/"

firstmaps = os.listdir(firstsource)
secondmaps = os.listdir(secondsource)

predictsource = '/Users/tunder/Dropbox/pagedata/production/predicts/'

predicts = os.listdir(predictsource)

allfeatures = list()
accuracies = list()

for filename in predicts:
    mapname = filename.replace('.predict', '.map')
    cleanid = utils.pairtreelabel(filename.replace('.predict', ''))

    if mapname in firstmaps:
        firstpath = os.path.join(firstsource, mapname)
        if os.path.isfile(firstpath):
            with open(firstpath, encoding = 'utf-8') as f:
                filelines = f.readlines()
                success = True
        else:
            success = False
    elif mapname in secondmaps:
        secondpath = os.path.join(secondsource, mapname)
        if os.path.isfile(secondpath):
            with open(secondpath, encoding = 'utf-8') as f:
                filelines = f.readlines()
                success = True
        else:
            success = False
    else:
        success = False

    if not success:
        print("Failed to locate a match for " + filename)
        continue
    else:
        correctgenres = list()
        for line in filelines:
            line = line.rstrip()
            fields = line.split('\t')
            literalgenre = fields[1]
            if literalgenre in genretranslations:
                functionalgenre = genretranslations[literalgenre]
            else:
                functionalgenre = literalgenre

            # Necessary because we are not attempting to discriminate all the categories
            # we manually recorded.

            correctgenres.append(functionalgenre)

    filepath = os.path.join(predictsource, filename)
    predicted = Prediction(filepath)

    if cleanid in rows:
        predicted.addmetadata(cleanid, table)
    else:
        print('Missing metadata for ' + cleanid)
        predicted.missingmetadata()

    matchpercent = predicted.match(correctgenres)
    allfeatures.append(predicted.getfeatures())
    accuracies.append(matchpercent)

featurearray = np.array(allfeatures)
numinstances, numfeatures = featurearray.shape

# Now let's normalize features by centering on mean and scaling
# by standard deviation

means = list()
stdevs = list()

for featureidx in range(numfeatures):
    thiscolumn = featurearray[ : , featureidx]
    thismean = np.mean(thiscolumn)
    means.append(thismean)
    thisstdev = np.std(thiscolumn)
    stdevs.append(thisstdev)
    featurearray[ : , featureidx] = (thiscolumn - thismean) / thisstdev

data = pd.DataFrame(featurearray)

logisticmodel = LogisticRegression(C = 1)
logisticmodel.fit(data, accuracies)

featurelist = ['confirmfic', 'denyfic', 'confirmpoe', 'denypoe', 'confirmdra', 'denydra', 'confirmnon', 'denynon', 'maxratio', 'rawflipratio', 'smoothflips', 'avggap', 'maxprob']

coefficients = list(zip(logisticmodel.coef_[0], featurelist))
coefficients.sort()
for coefficient, word in coefficients:
    print(word + " :  " + str(coefficient))

selfpredictions = logisticmodel.predict(data)
print("Pearson for whole data: ")
print(pearsonr(accuracies, selfpredictions))

folds = list()

for i in range(0, 350, 50):
    trainingset = pd.concat([data[0:i], data[i+50:]])
    trainingacc = accuracies[0:i] + accuracies[i+50:]
    testset = data[i: i + 50]
    testacc = accuracies[i : i + 50]
    newmodel = LogisticRegression(C = 1)
    newmodel.fit(trainingset, trainingacc)

    test = newmodel.predict(testset)
    print()
    print('Pearson for test set:' )
    print(pearsonr(testacc, test))
    folds.append(pearsonr(testacc, test)[0])

print()
print(sum(folds) / len(folds))

# I realize this isn't technically a perfect cross-validation, because the
# 13 data rows beyond 400 never get tested. But jeez. We're just getting
# a ballpark estimate here.






