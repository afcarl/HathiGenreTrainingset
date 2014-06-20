# CreateStupidPredictions.py

import os, sys
import SonicScrewdriver as utils

rowindices, columns, metadata = utils.readtsv("/Users/tunder/Dropbox/PythonScripts/hathimeta/ExtractedMetadata.tsv")

sourcedirectory = "/Users/tunder/Dropbox/pagedata/mixedtraining/genremaps/"

dirlist = os.listdir(sourcedirectory)

validnames = list()

for filename in dirlist:
    if not (filename.startswith(".") or filename.startswith("_")):
        validnames.append(filename)

for filename in validnames:
    filepath = os.path.join(sourcedirectory, filename)

    with open(filepath, mode="r", encoding="utf-8") as f:
        filelines = f.readlines()

    numpages = len(filelines)

    htid = utils.pairtreelabel(filename[0:-4])
    # convert the htid into a dirty pairtree label for metadata matching

    genre = "unknown"

    if htid in rowindices:

        genrestring = metadata["genres"][htid]
        genreinfo = genrestring.split(";")
        # It's a semicolon-delimited list of items.

        for info in genreinfo:

            if info == "Not fiction":
                genre = "non"

            if info == "Fiction" or info == "Novel" or info == "Novels":
                genre ="fic"

            if info == "Biography" or info == "Autobiography":
                genre = "bio"

            if info == "Poetry" or info == "Poems":
                genre = "poe"

            if info == "Drama" or info == "Tragedies" or info == "Comedies":
                genre = "dra"

            if info == "Catalog" or info == "Dictionary" or info == "Bibliographies":
                genre = "non"

        title = metadata["title"][htid].lower()
        titlewords = title.split()

        if "tale" in titlewords:
            genre = "fic"

        if "poems" in titlewords or "ballads" in titlewords:
            genre = "poe"

        if "comedy" in titlewords or "tragedy" in titlewords or "plays" in titlewords:
            genre = "dra"

    if genre == "unknown":
        genre = "non"

    pagelist = [genre] * numpages
    if numpages > 100:
        pagelist[0:4] = ["front"] * 5
        pagelist[-4:] = ["back"] * 5

    outpath = os.path.join("/Volumes/TARDIS/output/stupid/", filename[0:-4] + ".predict")
    with open(outpath, mode = "w", encoding = "utf-8") as f:
        for i in range(numpages):
            f.write(str(i) + '\t' + pagelist[i] + '\t' + pagelist[i] + '\n')



