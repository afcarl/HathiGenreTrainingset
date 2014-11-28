# Enrich metadata

# Our genre metadata needs to be enriched with information about the total
# number of pages in volumes, and the number in a relevant genre.

import os, csv, json
import SonicScrewdriver as utils

genrenames = {'dra': 'drama', 'fic': 'fiction', 'poe': 'poetry'}
rootpath = '/Volumes/TARDIS/maps/'
branches = ('18c', '19c', '20cPre1923')

header = ['htid', 'recordid', 'oclc', 'locnum', 'author', 'imprint', 'datetype', 'startdate', 'enddate', 'imprintdate', 'place', 'enumcron', 'subjects', 'title', 'prob80acc', 'prec>95pct', 'genrecounts', 'totalcounts', 'genreratio']

def make_row(htid, dirtyhtid, columns, table):

    columns_to_exclude = ['materialtype', 'genres']
    # I'm not repeating these columns, because the first is not useful and the second
    # is not reliable.

    outrow = [htid]
    for column in columns[1:]:
        if column not in columns_to_exclude:
            outrow.append(table[column][dirtyhtid])

    return outrow

metadata_path = '/Volumes/TARDIS/work/metadata/MergedMonographs.tsv'
rows, columns, table = utils.readtsv(metadata_path)

indextorows = dict()
for row in rows:
    cleanid = utils.pairtreefile(row)
    newrow = make_row(cleanid, row, columns, table)
    indextorows[cleanid] = newrow

for genreabbrev, genre in genrenames.items():

    print(genre)

    genrepath = os.path.join(rootpath, genre)

    volsinsubset = list()
    # Because there are some volumes in the metadata that weren't
    # included in the 95-percent subset. Those won't be present
    # as files, and shouldn't be carried forward to the next stage.
    metadataforgenre = dict()

    for branch in branches:
        # I've divided the files in each genre by century, which
        # creates a bit of unnecessary inconvenience.

        fullbranch = branch + genreabbrev
        print(branch)
        subdirectory = os.path.join(genrepath, fullbranch)
        filesinsubdir = os.listdir(subdirectory)
        for filename in filesinsubdir:
            if filename.startswith('.'):
                continue

            htid = filename.replace('.json', '')
            if htid not in indextorows:
                print('Missing metadata for file ' + filename)
                continue

            filepath = os.path.join(subdirectory, filename)
            with open(filepath, encoding = 'utf-8') as f:
                jobj = json.loads(f.read())

            if genre in jobj:
                genreobj = jobj[genre]
                precision = genreobj[genreabbrev + '_precision@prob']
                probability = genreobj['prob_' + genreabbrev + '>80precise']

            genrecounts = jobj['added_metadata']['genre_counts']
            if genreabbrev in genrecounts:
                thiscount = genrecounts[genreabbrev]
            else:
                thiscount = 0
                print(filename + ' anomalously has no pages for ' + genre)

            totalcounts = jobj['added_metadata']['totalpages']
            if totalcounts < 1:
                totalcounts = 1
                print('Total page count for ' + filename + ' is anomalously less than one.')

            ratio = int((thiscount / totalcounts) * 1000) / 1000

            metadataforgenre[htid] = indextorows[htid]
            metadataforgenre[htid].extend([probability, precision, thiscount, totalcounts, ratio])
            volsinsubset.append(htid)

    newmetadatapath = os.path.join(genrepath, (genreabbrev + '_subset.csv'))

    with open(newmetadatapath, mode = 'w', encoding = 'utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for vol in volsinsubset:
            row = metadataforgenre[vol]
            writer.writerow(row)










