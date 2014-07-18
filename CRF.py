# CRF.py
#
# Create training data for postprocessing
#
# We assemble models into an ensemble and then use contextual
# information to evaluate, for each page, the likelihood that
# the consensus prediction is wrong. This script creates
# training data for the process.

import SonicScrewdriver as utils
import EnsembleModule

from Coalescer import Volume
from Coalescer import Chunk

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

mclass = 0
rclass = 0
nclass = 0
pclass = 0


outputfile = "/Users/tunder/Dropbox/pagedata/errors.arff"

nominalattributes = ["thisgenre", "prevgenre", "runupgenre", "nextgenre"]
numericattributes = ["thislen", "prevlen", "nextlen", "dissent", "runupisprev", "runupisnext", "previsnext", "genreproportion", "runupproportion", "probthis", "probrunup"]

with open(outputfile, mode="w", encoding="utf-8") as f:
    f.write("% 1. Title: Training set for CRF.\n")
    f.write("\n")
    f.write("@RELATION crf")
    f.write("\n")
    for attribute in sorted(nominalattributes):
        f.write("@ATTRIBUTE " + attribute + "\t{begin,end,ads,bio,dra,fic,poe,non,front,back}\n")
    for attribute in sorted(numericattributes):
        f.write("@ATTRIBUTE " + attribute + "\tNUMERIC\n")
    f.write("@ATTRIBUTE id\tNUMERIC\n")
    f.write("@ATTRIBUTE class\t{model,runnerup,prev,next}\n")
    f.write("\n")
    f.write("@DATA\n")

consensus, secondthoughts, pageprobsforfile, dissentsequences, groundtruths = EnsembleModule.main()

idcounter = 0

for htid, predictedgenres in consensus.items():
    thisvolume = Volume(predictedgenres)
    chunklist = thisvolume.getchunklist()
    runnersup = secondthoughts[htid]
    pageprobs = pageprobsforfile[htid]
    dissentseq = dissentsequences[htid]
    groundtruth = groundtruths[htid]

    assert len(dissentseq) == len(predictedgenres)
    assert len(pageprobs) == len(predictedgenres)
    assert len(runnersup) == len(predictedgenres)

    features = list()

    # We want to create a list that is the same length as predictedgenres,
    # where each item maps to a page in predictedgenres and holds the index
    # of the "chunk" it belongs to. E.g.
    # [front, front, non, non, non, fic, non, non, back]
    # would map to
    # [0, 0, 1, 1, 1, 2, 3, 3, 4]

    chunkindices = list()
    chunkctr = 0
    for chunk in chunklist:
        for i in range(chunk.startpage, chunk.endpage):
            chunkindices.append(chunkctr)
        chunkctr += 1

    assert len(chunkindices) == len(predictedgenres)

    # We create a dictionary of genre countrs for this
    # volume in order to assess each genre's prevalence.
    genrecounts = sequence_to_counts(predictedgenres)
    genreproportions = normalize_dict(genrecounts)

    features = list()

    for i in range(len(predictedgenres)):
        chunkidx = chunkindices[i]

        thispage = dict()

        thispage["thisgenre"] = predictedgenres[i]
        thispage["thislen"] = chunklist[chunkidx].getlen()

        if chunkidx == 0:
            thispage["prevgenre"] = "begin"
            thispage["prevlen"] = 0
        else:
            thispage["prevgenre"] = chunklist[chunkidx - 1].genretype
            thispage["prevlen"] = chunklist[chunkidx - 1].getlen()

        if chunkidx == len(chunklist) - 1:
            thispage["nextgenre"] = "end"
            thispage["nextlen"] = 0
        else:
            thispage["nextgenre"] = chunklist[chunkidx + 1].genretype
            thispage["nextlen"] = chunklist[chunkidx + 1].getlen()

        thispage["runupgenre"] = runnersup[i]
        thispage["dissent"] = dissentseq[i]

        if thispage["runupgenre"] == thispage["thisgenre"]:
            thispage["runupgenre"] = nexthighest(pageprobs[i])

        if are_equal(thispage["runupgenre"], thispage["prevgenre"]):
            thispage["runupisprev"] = 1
        else:
            thispage["runupisprev"] = 0

        if are_equal(thispage["runupgenre"], thispage["nextgenre"]):
            thispage["runupisnext"] = 1
        else:
            thispage["runupisnext"] = 0

        if are_equal(thispage["prevgenre"], thispage["nextgenre"]):
            thispage["previsnext"] = 1
        else:
            thispage["previsnext"] = 0

        thispage["genreproportion"] = genreproportions[thispage["thisgenre"]]

        if thispage["runupgenre"] in genreproportions:
            thispage["runupproportion"] = genreproportions[thispage["runupgenre"]]
        else:
            thispage["runupproportion"] = 0

        thispage["probthis"] = pageprobs[i][thispage["thisgenre"]]
        thispage["probrunup"] = pageprobs[i][thispage["runupgenre"]]

        if are_equal(groundtruth[i], predictedgenres[i]):
            thispage["class"] = "model"
            mclass += 1
            # the model was right
        elif are_equal(groundtruth[i], thispage["runupgenre"]):
            thispage["class"] = "runnerup"
            rclass += 1
            # the runner-up to model prediction was right
        elif are_equal(groundtruth[i], thispage["prevgenre"]):
            thispage["class"] = "prev"
            pclass += 1
            # the page should continue previous segment's genre
        elif are_equal(groundtruth[i], thispage["nextgenre"]):
            thispage["class"] = "next"
            nclass += 1
            # the page should already be in next segment's genre
        else:
            thispage["class"] = "model"
            mclass += 1
            # because we don't know how to solve this, so leave it.

        features.append(thispage)

        # End page loop.

    # End volume loop.

    # Write features for this volume.

    with open(outputfile, mode="a", encoding="utf=8") as f:
        for page in features:
            outputline = ""
            for attribute in sorted(nominalattributes):
                outputline = outputline + page[attribute] + ","
            for attribute in sorted(numericattributes):
                outputline = outputline + str(page[attribute]) + ","
            outputline = outputline + str(idcounter) + ","
            outputline = outputline + page["class"] + "\n"
            f.write(outputline)

    idcounter += 1
    ## We have a unique value of this counter for each volume.

print("Done.\a")

