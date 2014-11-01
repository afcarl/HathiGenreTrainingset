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

def intpart(afloat):
    idx = (int(afloat*100))
    if idx < 0:
        idx = 0
    if idx > 99:
        idx = 99
    return idx

def calibrate(probability, curveset):
    idx = intpart(probability)
    precision = curveset['precision'][idx]
    recall = curveset['recall'][idx]
    return str(idx/100), precision, recall

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

    def getpredictions(self):
        pagedict = dict()
        for idx, genre in enumerate(self.smoothPredictions):
            pagedict[idx] = genre
        return pagedict

    def getmetadata(self):
        metadict = dict()
        metadict['htid'] = self.dirtyid
        metadict['author'] = self.author
        metadict['title'] = self.title
        metadict['inferred_date'] = self.date
        genrelist = []
        for genre in self.genres:
            if genre == "NotFiction":
                continue
            if genre == "UnknownGenre":
                continue
            if genre == "ContainsBiogMaterial":
                continue

            # In my experience, none of those tags are reliable in my Hathi dataset.

            genrelist.append(genre.lower())

        metadata['genre_tags'] = ", ".join(genrelist)
        return metadata


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

fullnames = {'fic': 'fiction', 'poe': 'poetry', 'dra': 'drama'}

# The logistic models we train on volumes are technically
# predicting the probability that an individual volume will
# cross a particular accuracy threshold. For the overall model
# it's .95, for the genres it's .8.

# This doesn't tell us what we really want to know, which is,
# if we construct a corpus of volumes like this, what will our
# precision and recall be? To infer that, we calculate precision
# and recall in the test set using different probability-thresholds,
# smooth the curve, and then use it empiricially to map a
# threshold-probability to a corpus level prediction for precision and recall.

genrestocalibrate = ['overall', 'fic', 'poe', 'dra']

calibration = dict()
for genre in genrestocalibrate:
    calibration[genre] = dict()
    calibration[genre]['precision'] = list()
    calibration[genre]['recall'] = list()

calipath = os.path.join(modeldir, 'calibration.csv')
with open(calipath, encoding = 'utf-8') as f:
    reader = csv.reader(f)
    next(reader, None)
    for row in reader:
        for idx, genre in enumerate(genrestocalibrate):
            calibration[genre]['precision'].append(row[idx * 2])
            calibration[genre]['recall'].append(row[(idx * 2) + 1])

outputdir = args[2]

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

        jsontemplate = dict()

        jsontemplate['page_genres'] = predicted.getpredictions()
        jsontemplate['hathi_metadata'] = predicted.getmetadata()
        jsontemplate['added_metadata'] = dict()
        jsontemplate['added_metadata']['totalpages'] = str(predicted.pagelen)
        jsontemplate['added_metadata']['maxgenre'] = str(predicted.maxgenre)
        jsontemplate['added_metadata']['genre_counts'] = str(predicted.genrecounts)

        overallprob, overallprecision, overallrecall = calibrate(overall95proba, calibration['overall'])

        overallaccuracy = dict()
        overallaccuracy['prob_95acc'] = overallprob
        overallaccuracy['cut_here_precision'] = overallprecision
        overallaccuracy['cut_here_recall'] = overallrecall

        jsontemplate['volume_accuracy'] = overallaccuracy

        for genre in genrestocheck:
            if genre in predicted.genrecounts:
                gpages = predicted.genrecounts[genre]
                gpercent = round((gpages / predicted.pagelen) * 100) / 100
                gprob, gprecision, grecall = calibrate(genreprobs[genre], calibration[genre])
                name = fullnames[genre]
                newdict = dict()
                newdict['prob_80acc'] = gprob
                newdict['pages_' + name] = gpages
                newdict['pct_' + name] = gpercent
                newdict['cut_here_precision'] = gprecision
                newdict['cut_here_recall'] = grecall
                jsontemplate[name] = newdict

        prefix = filename.split('.')[0]

        subdirectory = os.path.join(outputdir, prefix)
        if not os.path.isdir(subdirectory):
            os.mkdir(subdirectory)

        outpath = os.path.join(subdirectory, filename + ".json")
        with open(outpath, mode = 'w', encoding = 'utf-8') as f:
            f.write(json.dumps(jsontemplate, sort_keys = True))

