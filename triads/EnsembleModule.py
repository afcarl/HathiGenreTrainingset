# EnsembleModule.py

# Based on Ensemble.py; refactoring it a little to permit it's
# being called from another module.

import os
import numpy as np
import pandas as pd
from scipy.stats.stats import pearsonr
import SonicScrewdriver as utils
import MetadataCascades as cascades
import Coalescer
from math import log
import statsmodels.api as sm
import ConfusionMatrix
import random

def pairtreelabel(htid):
    ''' Given a clean htid, returns a dirty one that will match
    the metadata table.'''

    if '+' in htid or '=' in htid:
        htid = htid.replace('+',':')
        htid = htid.replace('=','/')

    return htid

def get_ground_truth_file(filename):
    '''Just returns a filename.'''

    if not ".predict" in filename:
        return ""

    htid = filename[0:-8]

    groundtruthversion = htid + ".map"
    return groundtruthversion

def get_ground_truth(gtfile, groundtruthdir, genretranslations):

    correctlist = list()

    gtfilepath = os.path.join(groundtruthdir, gtfile)
    with open(gtfilepath,encoding = "utf-8") as f:
        filelines = f.readlines()

    for line in filelines:
        line = line.rstrip()
        fields = line.split('\t')
        genre = fields[1]
        if genre in genretranslations:
            genre = genretranslations[genre]

        correctlist.append(genre)

    return correctlist

def interpret_probabilities(listoffields):
    probdict = dict()
    for field in listoffields:
        parts = field.split("::")
        genre = parts[0]

        try:
            probability = float(parts[1])
        except:
            probability = 0
            print("Float conversion error!")

        probdict[genre] = probability
    return probdict

def maxkey(dictionary):
    tuplelist = utils.sortkeysbyvalue(dictionary, whethertoreverse = True)
    winner = tuplelist[0][1]
    # if winner == "bio":
    #   winner = "non"
    return winner

def resolve_voting(votes, tiebreaker):
    electorate = len(votes)

    results = dict()
    for vote in votes:
        # if vote == "bio":
        #   vote = "non"
        utils.addtodict(vote, 1, results)
    candidate = utils.sortkeysbyvalue(results, whethertoreverse = True)

    dissent = (electorate - candidate[0][0]) / electorate

    if len(candidate) < 2:
        # There is only one candidate.
        return candidate[0][1], dissent, candidate[0][1]

    elif candidate[0][0] > candidate[1][0]:
        # We have a majority.
        return candidate[0][1], dissent, candidate[1][1]

    else:
        # We have a tie.
        if tiebreaker == candidate[0][1]:
            print("Tiebreaker " + tiebreaker)
            return candidate[0][1], dissent, candidate[1][1]
        elif tiebreaker == candidate[1][1]:
            print("Tiebreaker " + tiebreaker)
            return candidate[1][1], dissent, candidate[0][1]
        else:
            print("Tie in spite of " + tiebreaker)
            win = random.choice([candidate[0][1], candidate[1][1]])
            if win == candidate[0][1]:
                runnerup = candidate[1][1]
            else:
                runnerup = candidate[0][1]

            return win, dissent, runnerup

def genresareequal(truegenre, predictedgenre):
    arethesame = ["bio", "trv", "aut", "non"]
    alsothesame = ["back", "index", "front", "ads"]
    if truegenre == predictedgenre:
        return True
    elif truegenre in arethesame and predictedgenre in arethesame:
        return True
    elif truegenre in alsothesame and predictedgenre in alsothesame:
        return True
    else:
        return False

def compare_two_lists(truelist, predicted, wordsperpage, whethertocountwords):
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

        if whethertocountwords:
            increment = wordsperpage[index]
        else:
            increment = 1

        utils.addtodict(truegenre, increment, totaltruegenre)

        predictedgenre = predicted[index]

        if genresareequal(truegenre, predictedgenre):
            utils.addtodict(truegenre, increment, correctbygenre)
            accurate += increment
        else:
            utils.addtodict((truegenre, predictedgenre), increment, errorsbygenre)
            inaccurate += increment

    return totaltruegenre, correctbygenre, errorsbygenre, accurate, inaccurate

def add_dictionary(masterdict, dicttoadd):
    for key, value in dicttoadd.items():
        if key in masterdict:
            masterdict[key] += value
        else:
            masterdict[key] = value
    return masterdict

def nix_a_genre(firstthoughts, genretonix, secondthoughts):
    returnsequence = list()
    assert len(firstthoughts) == len(secondthoughts)

    for i in range(len(firstthoughts)):
        genre = firstthoughts[i]
        if genre == genretonix:
            returnsequence.append(secondthoughts[i])
        else:
            returnsequence.append(genre)

    return returnsequence

# BEGIN MAIN.

def main(listofmodels = ["newfeatures6", "newfeatures2", "newfeatures3", "newfeatures4", "newfeatures9", "forest", "bycallno", "forest4", "forest7"]):

    genretranslations = {'subsc' : 'front', 'argum': 'non', 'pref': 'non', 'aut': 'bio', 'bio': 'bio', 'toc': 'front', 'title': 'front', 'bookp': 'front', 'bibli': 'back', 'gloss': 'back', 'epi': 'fic', 'errat': 'non', 'notes': 'non', 'ora': 'non', 'let': 'bio', 'trv': 'non', 'lyr': 'poe', 'nar': 'poe', 'vdr': 'dra', 'pdr': 'dra', 'clo': 'dra', 'impri': 'front', 'libra': 'back', 'index': 'back'}

    predictroot = "/Volumes/TARDIS/output/"
    firstdir = predictroot + listofmodels[0] + "/"
    predictfiles = os.listdir(firstdir)

    validfiles = list()

    for filename in predictfiles:
        if filename.endswith(".predict"):
            validfiles.append(filename)

    groundtruthdir = "/Users/tunder/Dropbox/pagedata/newfeatures/genremaps/"

    groundtruthfiles = os.listdir(groundtruthdir)

    groundtruths = dict()
    htidtable = dict()
    for filename in validfiles:
        gt = get_ground_truth_file(filename)
        if not gt in groundtruthfiles:
            continue
        htid = gt[0:-4]
        htidtable[filename] = htid
        if gt != "":
            groundtruth = get_ground_truth(gt, groundtruthdir, genretranslations)
            groundtruths[htid] = groundtruth

    dissensus = dict()
    pageprobsforfile = dict()

    for filename in validfiles:
        htid = htidtable[filename]
        versions = list()
        pageprobs = list()
        for model in listofmodels:
            try:
                thispath = predictroot + model + "/" + filename
                with open(thispath, encoding="utf-8") as f:
                    filelines = f.readlines()

                if len(pageprobs) < len(filelines):
                    # Initialize page probabilities to correct length.
                    if len(pageprobs) > 0:
                        print("Initializing more than once. Error condition.")
                    for i in range(len(filelines)):
                        newdict = dict()
                        pageprobs.append(newdict)

                smoothlist = list()
                roughlist = list()
                for i in range(len(filelines)):
                    line = filelines[i]
                    line = line.rstrip()
                    fields = line.split('\t')
                    rough = fields[1]
                    smoothed = fields[2]
                    smoothlist.append(smoothed)
                    roughlist.append(rough)
                    if len(fields) > 5:
                        probdict = interpret_probabilities(fields[5:])
                        utils.add_dicts(probdict, pageprobs[i])
                        # This will add all the probabilities for this page to the
                        # record of per-page probabilities.

                versions.append(smoothlist)
                versions.append(roughlist)
            except:
                pass
        pageprobsforfile[htid] = pageprobs

        dissensus[htid] = [x for x in zip(*versions)]

    consensus = dict()
    dissentperfile = dict()
    secondthoughts = dict()
    dissentsequences = dict()

    for htid, pagelist in dissensus.items():
        winners = list()
        runnersup = list()
        dissentseq = list()
        pageprobs = pageprobsforfile[htid]
        for i in range(len(pagelist)):
            page = pagelist[i]
            floatwinner = maxkey(pageprobs[i])
            winner, dissent, runnerup = resolve_voting(page, floatwinner)
            winners.append(winner)
            runnersup.append(runnerup)
            dissentseq.append(dissent)
        consensus[htid] = winners
        secondthoughts[htid] = runnersup
        dissentsequences[htid] = dissentseq

    return consensus, secondthoughts, pageprobsforfile, dissentsequences, groundtruths
