# Figures out what call numbers mean for genre

import os, sys
import SonicScrewdriver as utils

rowindices, columns, metadata = utils.readtsv("/Users/tunder/Dropbox/pagedata/metascrape/EnrichedMetadata.tsv")

options = ["non", "bio", "poe", "dra", "fic"]

modelindices, modelcolumns, modeldata = utils.readtsv("/Users/tunder/Dropbox/PythonScripts/hathimeta/newgenretable.txt")

def keywithmaxval(dictionary):
    maxval = 0
    maxkey = ""

    for key, value in dictionary.items():
        if value > maxval:
            maxval = value
            maxkey = key

    return maxkey

def sequence_to_counts(genresequence):
    '''Converts a sequence of page-level predictions to
    a dictionary of counts reflecting the number of pages
    assigned to each genre. Also reports the largest genre.'''

    genrecounts = dict()
    genrecounts['fic'] = 0
    genrecounts['poe'] = 0
    genrecounts['dra'] = 0
    genrecounts['non'] = 0

    for page in genresequence:
        indexas = page

        # For this purpose, we treat biography and indexes as equivalent to nonfiction.
        if page == "bio" or page == "index" or page == "back" or page == "trv":
            indexas = "non"

        utils.addtodict(indexas, 1, genrecounts)

    # Convert the dictionary of counts into a sorted list, and take the max.
    genretuples = utils.sortkeysbyvalue(genrecounts, whethertoreverse = True)
    maxgenre = genretuples[0][1]

    return genrecounts, maxgenre

def maxoption(fivetuple):
    maxcol = 0
    maxval = 0.0
    nexthighest = 0
    for i in range(5):
        if float(fivetuple[i]) > maxval:
            nexthighest = maxval
            maxval = float(fivetuple[i])
            maxcol = i
    if maxval > 0.94 and nexthighest < 0.4:
        return maxcol
    else:
        return -1

def choose_cascade(htid):
    '''Reads metadata about this volume and uses it to decide what metadata-level features should be assigned.'''

    global rowindices, columns, metadata, modelindices, modeldata


    probablydrama = False
    probablypoetry = False
    probablybiography = False
    probablyfiction = False
    maybefiction = False

    htid = utils.pairtreelabel(htid)
    # convert the clean pairtree filename into a dirty pairtree label for metadata matching

    if htid not in rowindices:
        # We have no metadata for this volume.
        print("Volume missing from ExtractedMetadata.tsv: " + htid)

    else:
        genrestring = metadata["genres"][htid]
        genreinfo = genrestring.split(";")
        # It's a semicolon-delimited list of items.

        for info in genreinfo:

            if info == "Biography" or info == "Autobiography":
                probablybiography = True

            if info == "Fiction" or info == "Novel":
                probablyfiction = True

            if (info == "Poetry" or info == "Poems"):
                probablypoetry = True

            if (info == "Drama" or info == "Tragedies" or info == "Comedies"):
                probablydrama = True

    if htid in modelindices:

        title = metadata["title"][htid].lower()
        titlewords = title.split()

        maxgenre = maxoption((modeldata["bio"][htid], modeldata["dra"][htid], modeldata["fic"][htid], modeldata["non"][htid], modeldata["poe"][htid]))

        if maxgenre == 4 and "poems" in titlewords or "poetical" in titlewords:
            probablypoetry = True

        if maxgenre == 1:
            probablydrama = True

        if maxgenre == 2:
            maybefiction = True

    return probablybiography, probablydrama, probablyfiction, probablypoetry, maybefiction

def letterpart(locnum):
    if locnum == "<blank>":
        return "<blank>"

    letterstring = ""
    for char in locnum:
        if char.isalpha():
            letterstring += char.upper()
        else:
            break
    if len(letterstring) > 2:
        letterstring = letterstring[:2]

    if len(letterstring) > 1 and letterstring[0] == "N":
        letterstring = "N"
    if len(letterstring) > 1 and letterstring[0] == "V":
        letterstring = "V"

    return letterstring

allLCs = dict()
bio = dict()
fic = dict()
poe = dict()
dra = dict()

ctr = 0
for rowidx in rowindices:

    loc = metadata["LOCnum"][rowidx]

    probablybiography, probablydrama, probablyfiction, probablypoetry, maybefiction = choose_cascade(rowidx)
    LC = letterpart(loc)

    utils.addtodict(LC, 1, allLCs)

    if probablybiography:
        utils.addtodict(LC, 1, bio)
    if probablydrama:
        utils.addtodict(LC, 1, dra)
    if probablyfiction:
        utils.addtodict(LC, 1, fic)
    if probablypoetry:
        utils.addtodict(LC, 1, poe)
    if maybefiction:
        utils.addtodict(LC, 0.1, fic)

    ctr += 1
    if ctr % 1000 == 1:
        print(ctr)

    if ctr > 100000:
        break

littuples = list()
biotuples = list()
fictuples = list()
poetuples = list()
dratuples = list()

print("Done reading data. Now creating tuples.")

ctr = 0
for key, totalcount in allLCs.items():

    totallit = dra.get(key, 0) + fic.get(key, 0) + poe.get(key, 0)
    litpercent = (totallit + 0.01) / (totalcount + 0.01)
    littuples.append((litpercent, key, totalcount))
    biopercent = (bio.get(key, 0) + 0.01) / (totalcount + 0.01)
    biotuples.append((biopercent, key, totalcount))
    totalfic = fic.get(key, 0)
    ficpercent = (totalfic + 0.01) / (totalcount + 0.01)
    fictuples.append((ficpercent, key, totalcount))
    totalpoe = poe.get(key, 0)
    poepercent = (totalpoe + 0.01) / (totalcount + 0.01)
    poetuples.append((poepercent, key, totalcount))
    totaldra = dra.get(key, 0)
    drapercent = (totaldra + 0.01) / (totalcount + 0.01)
    dratuples.append((drapercent, key, totalcount))

    ctr += 1
    if ctr % 1000 == 1:
        print(ctr)

print("Done creating tuples. Now sorting tuples.")

littuples.sort()
biotuples.sort()






