# randomsample
#
# The goal here is to randomly sample n pages from a list of books in a given genre,
# where some but not all of the pages in each book are in that genre. We want to
# be random *at the page level*. In other words, books with a lot of pages should
# have more chance of getting a page drawn than books with few. This is because
# we're testing the validity of the list for macroscopic research where larger
# books will in practice have more weight.

# But just to make things a little trickier, we want to stratify this by century.
# i.e, we want 100 randomly selected pages from each century.

import csv
from random import randint
import SonicScrewdriver as utils

TOSELECT = 100

centuries = dict()
centuries['18c'] = list()
centuries['19c'] = list()
centuries['20c'] = list()

with open('/Volumes/TARDIS/maps/fiction/fic_filtered.csv', encoding = 'utf-8') as f:
    reader = csv.reader(f)
    header = list()
    columns = dict()

    for row in reader:
        if len(header) < 1:
            # This is the first row in the file; we use it to create a
            # column index.
            header = row
            for idx, colhead in enumerate(header):
                columns[colhead] = idx

        else:
            htid = row[columns['htid']]
            genrecounts = int(row[columns['genrecounts']])
            # This is the number of pages *in the genre.*

            title = row[columns['title']]
            author = row[columns['author']]
            datetype = row[columns['datetype']]
            startdate = row[columns['startdate']]
            enddate = row[columns['enddate']]
            imprintdate = row[columns['imprintdate']]
            date = utils.infer_date(datetype, startdate, enddate, imprintdate)
            if date > 1699 and date < 1800:
                centuries['18c'].append((date, author, title, genrecounts, htid))
            elif date < 1900:
                centuries['19c'].append((date, author, title, genrecounts, htid))
            elif date < 1923:
                centuries['20c'].append((date, author, title, genrecounts, htid))

pagecenturies = dict()

for century, voltuples in centuries.items():
    # Each voltuple represent a volume.

    pagecenturies[century] = list()

    # For each list of volumes associated with a century, we construct an associated
    # list of pages for that century.

    # We now construct a list as long as voltuples, where each element records the floor of the
    # page range for the associated volume, in an imagined sequential ordering of pages for the
    # whole century. Note that we don't actually construct that list of pages.

    listoffloors = list()
    floor = 0

    for quintuple in voltuples:
        date, author, title, genrecounts, htid = quintuple
        listoffloors.append(floor)
        floor += genrecounts

    ceiling = floor
    # The floor of what *would* have been the next volume (if there were one) is the
    # ceiling of the whole sequence.

    for i in range(TOSELECT):
        # Randomly select a page in the sequence.
        pageidx = randint(0, ceiling)

        # Now let's find the index of the *floor* closest to that page.
        volindex, closestfloor = min(enumerate(listoffloors), key=lambda x: abs(x[1] - pageidx))

        # To get the right volume we want to make sure the floor is <= pageidx. The *closest*
        # floor after all might be above us.

        if closestfloor > pageidx:
            volindex = volindex - 1

        pgnuminvol = pageidx - listoffloors[volindex]
        # Note that this is the page number only in a sequence of pages-in-this-genre,
        # not the literal page number in the volume, which may include other genres.

        date, author, title, genrecounts, htid = voltuples[volindex]

        pagecenturies[century].append((htid, pgnuminvol))
        print(str(date) + ' || ' + author + ' || ' + title + ' || ' + str(pgnuminvol))














