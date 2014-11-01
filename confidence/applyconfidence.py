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
import pickle, csv

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

def normalizearray(featurearray):
    '''Normalizes an array by centering on means and
    scaling by standard deviations.
    '''

    numinstances, numfeatures = featurearray.shape
    means = list()
    stdevs = list()
    for featureidx in range(numfeatures):
        thiscolumn = featurearray[ : , featureidx]
        thismean = np.mean(thiscolumn)
        means.append(thismean)
        thisstdev = np.std(thiscolumn)
        stdevs.append(thisstdev)
        featurearray[ : , featureidx] = (thiscolumn - thismean) / thisstdev

    return featurearray

def normalizeformodel(featurearray, modeldict):
    '''Normalizes an array by centering on means and
    scaling by standard deviations associated with the given model.
    '''

    numinstances, numfeatures = featurearray.shape
    means = modeldict['means']
    stdevs = modeldict['stdevs']
    for featureidx in range(numfeatures):
        thiscolumn = featurearray[ : , featureidx]
        thismean = means[featureidx]
        thisstdev = stdevs[featureidx]
        featurearray[ : , featureidx] = (thiscolumn - thismean) / thisstdev

    return featurearray

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

        self.genrecounts, self.maxgenre = sequence_to_counts(self.smoothPredictions)
        pagesinmax = self.genrecounts[self.maxgenre]
        self.maxratio = pagesinmax / self.pagelen

        self.rawflipratio = (count_flips(self.rawPredictions) / self.pagelen)
        self.smoothflips = count_flips(self.smoothPredictions)

        if 'bio' in self.genrecounts and self.genrecounts['bio'] > (self.pagelen / 2):
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

    def genrefeatures(self, agenre):
        ''' Extracts features to characterize the likelihood of accuracy in a
        particular genre.
        '''

        if agenre in self.genrecounts:
            pagesingenre = self.genrecounts[agenre]
        else:
            pagesingenre = 0

        genreproportion = pagesingenre / self.pagelen

        features = np.zeros(8)

        if agenre == 'fic':

            if 'Fiction' in self.genres or 'Novel' in self.genres or 'Short stories' in self.genres:
                features[0] = 1

            if 'Drama' in self.genres or 'Poetry' in self.genres or self.nonmetaflag:
                features[1] = 1

        if agenre == 'poe':

            if 'Poetry' in self.genres or 'poems' in self.title.lower():
                features[0] = 1

            if 'Drama' in self.genres or 'Fiction' in self.genres or self.nonmetaflag:
                features[1] = 1

        if agenre == 'dra':

            if 'Drama' in self.genres or 'plays' in self.title.lower():
                features[0] = 1

            if 'Fiction' in self.genres or 'Poetry' in self.genres or self.nonmetaflag:
                features[1] = 1

        features[2] = genreproportion
        features[3] = self.rawflipratio
        features[4] = self.smoothflips
        features[5] = self.avggap
        features[6] = self.maxprob
        features[7] = self.maxratio

        return features

    def genreaccuracy(self, checkgenre, correctgenres):
        truepositives = 0
        falsepositives = 0

        for idx, genre in enumerate(self.smoothPredictions):
            if genre == checkgenre:

                if correctgenres[idx] == checkgenre:
                    truepositives += 1
                else:
                    falsepositives += 1

        if (truepositives + falsepositives) > 0:
            precision = truepositives / (truepositives + falsepositives)
        else:
            precision = 1000
            # which we shall agree is a signal that this is meaningless

        return precision

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

        return matches / self.pagelen, matches, self.pagelen

    def matchgenres(self, correctgenres):
        ''' Calculate true positives, false positives, true negatives, and false
        negatives for three genres. You're looking at this wordy code and saying
        "dude, you could have constructed an array," and you are correct. That would
        have been better in every respect.
        However, I didn't.
        '''
        poetryTP = 0
        poetryFP = 0
        poetryTN = 0
        poetryFN = 0
        fictionTP = 0
        fictionFP = 0
        fictionTN = 0
        fictionFN = 0
        dramaTP = 0
        dramaTN = 0
        dramaFP = 0
        dramaFN = 0

        assert len(correctgenres) == len(self.smoothPredictions)

        for idx, genre in enumerate(self.smoothPredictions):

            if correctgenres[idx] == 'poe':
                if genre == 'poe':
                    poetryTP += 1
                else:
                    poetryFN += 1

            if correctgenres[idx] != 'poe':
                if genre == 'poe':
                    poetryFP += 1
                else:
                    poetryTN += 1

            if correctgenres[idx] == 'fic':
                if genre == 'fic':
                    fictionTP += 1
                else:
                    fictionFN += 1

            if correctgenres[idx] != 'fic':
                if genre == 'fic':
                    fictionFP += 1
                else:
                    fictionTN += 1

            if correctgenres[idx] == 'dra':
                if genre == 'dra':
                    dramaTP += 1
                else:
                    dramaFN += 1

            if correctgenres[idx] != 'dra':
                if genre == 'dra':
                    dramaFP +=1
                else:
                    dramaTN +=1


        return poetryTP, poetryFP, poetryTN, poetryFN, fictionTP, fictionFP, fictionTN, fictionFN, dramaTP, dramaFP, dramaTN, dramaFN

    def matchvector(self, correctgenres):
        assert len(correctgenres) == len(self.smoothPredictions)
        matches = list()
        for idx, genre in enumerate(self.smoothPredictions):
            if correctgenres[idx] == genre:
                matches.append(1)
            elif correctgenres[idx] == 'bio' and genre == 'non':
                matches.append(1)
            elif correctgenres[idx] == 'non' and genre == 'bio':
                matches.append(1)
            else:
                matches.append(0)

        return matches

# Begin main script.

args = sys.argv

sourcedirlist = args[0]
modeldir = args[1]

genrestocheck = ['fic', 'poe', 'dra']
genrepath = dict()
genremodel = dict()

overallpath = os.path.join(modeldir, 'overallmodel.p')
genrepath['fic'] = os.path.join(modeldir, 'ficmodel.p')
genrepath['dra'] = os.path.join(modeldir, 'dramodel.p')
genrepath['poe'] = os.path.join(modeldir, 'poemodel.p')

with open(overallpath, mode='rb') as f:
    overallmodel = pickle.load(f)

for genre in genrestocheck:
    with open(genrepath[genre], mode='rb') as f:
        genremodel[genre] = pickle.load(f)


TOL = 0.1
THRESH = 0.80

metadatapath = '/projects/ichass/usesofscale/hathimeta/MergedMonographs.tsv'
rows, columns, table = utils.readtsv(metadatapath)

for sourcedir in sourcedirlist:
    predicts = os.listdir(predictsource)
    predicts = [x for x in predicts if not x.startswith('.')]

    for filename in predicts:
        cleanid = utils.pairtreelabel(filename.replace('.predict', ''))
        filepath = os.path.join(predictsource, filename)

        try:
            predicted = Prediction(filepath)
        except:
            print("Failure to load prediction from " + filepath)
            continue

        if cleanid in rows:
            predicted.addmetadata(cleanid, table)
        else:
            print('Missing metadata for ' + cleanid)
            predicted.missingmetadata()

        overallfeatures = predicted.getfeatures()
        featurearray = normalizeformodel(np.array(overallfeatures), overallmodel)
        featureframe = pd.DataFrame(featurearray)
        thismodel = overallmodel['model']
        overall95proba = thismodel.predict_proba(testset)[0][1]

        genreprobs = dict()

        for genre in genrestocheck:
            features = predicted.genrefeatures(genre)
            featurearray = normalizeformodel(np.array(features), genremodel[genre])
            featureframe = pd.DataFrame(featurearray)
            thismodel = genremodel[genre]['model']
            genreprobs[genre] = thismodel.predict_proba(testset)[0][1]


poetryTPs = np.array(poetryTPs)
poetryFPs = np.array(poetryFPs)
poetryTNs = np.array(poetryTNs)
poetryFNs = np.array(poetryFNs)

fictionTPs = np.array(fictionTPs)
fictionFPs = np.array(fictionFPs)
fictionTNs = np.array(fictionTNs)
fictionFNs = np.array(fictionFNs)

dramaTPs = np.array(dramaTPs)
dramaFPs = np.array(dramaFPs)
dramaTNs = np.array(dramaTNs)
dramaFNs = np.array(dramaFNs)

# Now let's normalize features by centering on mean and scaling
# by standard deviation

featurearray, means, stdevs = normalizeandexport(featurearray)

data = pd.DataFrame(featurearray)

binarized = binarize(accuracies, threshold = THRESH)

logisticmodel = LogisticRegression(C = TOL)
logisticmodel.fit(data, binarized)

featurelist = ['confirmfic', 'denyfic', 'confirmpoe', 'denypoe', 'confirmdra', 'denydra', 'confirmnon', 'denynon', 'maxratio', 'rawflipratio', 'smoothflips', 'avggap', 'maxprob']

# featurelist = ['maxratio', 'rawflipratio', 'smoothflips', 'avggap', 'maxprob']

coefficients = list(zip(logisticmodel.coef_[0], featurelist))
coefficients.sort()
for coefficient, word in coefficients:
    print(word + " :  " + str(coefficient))

selfpredictions = logisticmodel.predict_proba(data)[ : , 1]
print("Pearson for whole data: ")
print(pearsonr(accuracies, selfpredictions))

# Now we export that model.

exportfolder = '/Users/tunder/output/confidencemodels/'
modelfile = exportfolder + "overallmodel.p"

wholemodel = dict()
wholemodel['model'] = logisticmodel
wholemodel['means'] = means
wholemodel['stdevs'] = stdevs
with open(modelfile, mode = 'wb') as f:
    pickle.dump(wholemodel, f)

predictions = np.zeros(len(data))

for i in range(0, len(data)):
    trainingset = pd.concat([data[0:i], data[i+1:]])
    trainingacc = binarized[0:i] + binarized[i+1:]
    testset = data[i: i + 1]
    newmodel = LogisticRegression(C = TOL)
    newmodel.fit(trainingset, trainingacc)

    predict = newmodel.predict_proba(testset)[0][1]
    predictions[i] = predict

print()
print('Pearson for test set:' )
print(pearsonr(predictions, accuracies))

genrepredictions = dict()
unpackedpredictions = dict()

# Now we produce predictions for each genre using a leave-one-out method. Otherwise we wouldn't
# know that the modeling strategy we're using was in reality reliable beyond this test set.

for genre in genrestocheck:
    print(genre)
    genrearray = np.array(genrefeatures[genre])
    genrearray = normalizearray(genrearray)
    gdata = pd.DataFrame(genrearray)
    numinstances, numfeatures = gdata.shape

    gbinary = binarize(genreprecisions[genre], threshold= THRESH)
    genrepredictions[genre] = leave1out(gdata, gbinary, tolparameter = TOL)
    unpackedpredictions[genre] = unpack(genrepredictions[genre], modeledvols[genre])

# However, we also want to produce models that can be exported. This we don't have to do using a
# leave-one-out method.

for genre in genrestocheck:
    print(genre + " exporting model. ")
    genrearray = np.array(genrefeatures[genre])
    genrearray, means, stdevs = normalizeandexport(genrearray)
    gdata = pd.DataFrame(genrearray)
    gbinary = binarize(genreprecisions[genre], threshold= THRESH)
    genremodel = LogisticRegression(C = TOL)
    genremodel.fit(gdata, gbinary)
    predict = genremodel.predict(gdata)
    correlation = pearsonr(predict, gbinary)
    print("Pearson correlation of auto-prediction: " + str(correlation))
    # Don't really use that to assess accuracy of the model, because not
    # crossvalidated. Just using it to check that the code works.
    modelfile = exportfolder + genre + 'model.p'

    # The whole model is the model itself, plus the means and standard deviations
    # that were used to normalize the feature array.

    wholemodel = dict()
    wholemodel['model'] = genremodel
    wholemodel['means'] = means
    wholemodel['stdevs'] = stdevs

    with open(modelfile, mode = 'wb') as f:
        pickle.dump(wholemodel, f)

def testtwo(aseq, bseq, thresh):
    bothfail = 0
    afail = 0
    bfail = 0
    c = 0
    assert len(aseq) == len(bseq)
    for a,b in zip(aseq, bseq):
        if a < thresh and b< thresh:
            c += 1
            bothfail += 1
        elif a > thresh and b > thresh:
            c += 1
        elif a < thresh and b > thresh:
            afail += 1
        elif a > thresh and b < thresh:
            bfail += 1
        else:
            print('whoa')
            pass

    return c / len(aseq), afail, bfail, bothfail

def corpusaccuracy(predictions, correctpages, totalpages, threshold):
    allcorrect = np.sum(correctpages[predictions > threshold])
    alltotal = np.sum(totalpages[predictions > threshold])
    return allcorrect / alltotal

def corpusrecall(predictions, correctpages, totalpages, threshold):
    missedcorrect = np.sum(correctpages[predictions < threshold])
    correcttotal = np.sum(correctpages)
    return missedcorrect / correcttotal

def precision(genreTP, genreFP, genreTN, genreFN, predictions, threshold):
    truepos = np.sum(genreTP[predictions>threshold])
    falsepos = np.sum(genreFP[predictions>threshold])

    precision = truepos / (truepos + falsepos)

    falsenegs = np.sum(genreFN[predictions >= threshold])
    missedpos = np.sum(genreTP[predictions < threshold])
    missednegs = np.sum(genreFN[predictions < threshold])

    totalfalsenegs = falsenegs + missedpos + missednegs

    # Because the threshold also cuts things off.

    recall = truepos / (truepos + totalfalsenegs)

    return precision, recall


#plotresults
import matplotlib.pyplot as plt
precisions = list()
recalls= list()
for T in range(100):
    tr = T / 100
    p, r = precision(fictionTPs, fictionFPs, fictionTNs, fictionFNs, unpackedpredictions['fic'], tr)
    precisions.append(p)
    recalls.append(r)

poeprecisions = list()
poerecalls= list()
for T in range(100):
    tr = T / 100
    p, r = precision(poetryTPs, poetryFPs, poetryTNs, poetryFNs, unpackedpredictions['poe'], tr)
    poeprecisions.append(p)
    poerecalls.append(r)

draprecisions = list()
drarecalls = list()
for T in range(100):
    tr = T / 100
    p, r = precision(dramaTPs, dramaFPs, dramaTNs, dramaFNs, unpackedpredictions['dra'], tr)
    draprecisions.append(p)
    drarecalls.append(r)

with open('/Users/tunder/output/confidence80.csv', mode = 'w', encoding='utf-8') as f:
    writer = csv.writer(f)
    row = ['ficprecision', 'ficrecall', 'poeprecision', 'poerecall', 'draprecision', 'drarecall']
    writer.writerow(row)
    for idx in range(100):
        row = [precisions[idx], recalls[idx], poeprecisions[idx], poerecalls[idx], draprecisions[idx], drarecalls[idx]]
        writer.writerow(row)

