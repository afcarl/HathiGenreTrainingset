# Uses metadata to help assess degrees

import os, sys
import SonicScrewdriver as utils

rowindices, columns, metadata = utils.readtsv("/Users/tunder/Dropbox/pagedata/metascrape/EnrichedMetadata.tsv")

options = ["non", "bio", "poe", "dra", "fic"]

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

def choose_cascade(htid):
    '''Reads metadata about this volume and uses it to decide what metadata-level features should be assigned.'''

    global rowindices, columns, metadata


    probablydrama = False
    probablypoetry = False
    probablybiography = False
    probablyfiction = False
    locstartsP = False
    locnotP = False

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

        title = metadata["title"][htid].lower()
        titlewords = title.split()

        if "poems" in titlewords or "ballads" in titlewords or "poetical" in titlewords:
            probablypoetry = True

        loc = metadata["LOCnum"][htid]

        if (loc.startswith("P") and not loc.startswith("PE")) or loc.startswith("AC4"):
            locstartsP = True
        elif not loc.startswith("<"):
            locnotP = True


    return probablybiography, probablydrama, probablyfiction, probablypoetry, locstartsP, locnotP

sourcedir = "/Users/tunder/Dropbox/pagedata/newfeatures/oldfeatures/"

dirlist = os.listdir(sourcedir)

htids = list()

otherctr = 0
ctr = 0
for filename in dirlist:

    if len(filename) > 7 and not filename.startswith("."):
        stripped = filename[:-7]
        probablybiography, probablydrama, probablyfiction, probablypoetry, locstartsP, locnotP = choose_cascade(stripped)

        outpath = "/Users/tunder/Dropbox/pagedata/newfeatures/pagefeatures/" + filename

        with open(outpath, mode="w", encoding="utf-8") as f:
            if probablybiography:
                f.write("-1\t#metaBiography\t0\n")
                print("Probably bio: " + stripped)
            if probablydrama:
                f.write("-1\t#metaDrama\t0\n")
                print("Probably dra: " + stripped)
            if probablyfiction:
                f.write("-1\t#metaFiction\t0\n")
                print("Probably fic: " + stripped)
            if probablypoetry:
                f.write("-1\t#metaPoetry\t0\n")
                print("Probably poe: " + stripped)
            if locstartsP:
                f.write("-1\t#locstartsP\t0\n")
                print("Loc starts P: " + stripped)
                otherctr += 1
            if locnotP:
                f.write("-1\t#locnotP\t0\n")
                print("Loc NOT P: " + stripped)
                ctr += 1

        sourcepath = sourcedir + filename
        with open(sourcepath, encoding = 'utf-8') as f:
            filelines = f.readlines()

        with open(outpath, mode="a", encoding='utf-8') as f:
            for line in filelines:
                f.write(line)

print("NotP " + str(ctr))
print("P " + str(otherctr))

