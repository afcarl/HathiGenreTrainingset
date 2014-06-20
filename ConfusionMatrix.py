# ConfusionMatrix.py

import numpy
import pandas

def confusion_matrix(correctbygenre, errorsbygenre):
    ''' Function turns the dictionaries produced by
    Evaluate.py into a confusion matrix.'''

    genrelist = ["front", "ads", "back"]
    for genre in genrelist:
        if genre not in correctbygenre:
            correctbygenre[genre] = 0

    for genre, count in correctbygenre.items():
        if genre not in genrelist:
            genrelist.append(genre)
    numgenres = len(genrelist)

    predicted = dict()
    for genre in genrelist:
        newcolumn = dict()
        predicted[genre] = newcolumn

    for predictedgenre in genrelist:
        for truegenre in genrelist:
            if truegenre==predictedgenre:
                predicted[predictedgenre][truegenre] = correctbygenre[truegenre]
            else:
                tuplekey = (truegenre, predictedgenre)
                if tuplekey in errorsbygenre:
                    predicted[predictedgenre][truegenre] = errorsbygenre[tuplekey]
                else:
                    predicted[predictedgenre][truegenre] = 0

    confusion = pandas.DataFrame(predicted)

    newrow = dict()
    newcolumn = list()
    columngenres = [x for x in confusion.columns]

    for genre in columngenres:
        precision = correctbygenre[genre] / confusion[genre].sum()
        newrow[genre] = {'precision': precision}
        recall = correctbygenre[genre] / confusion.loc[genre].sum()
        newcolumn.append(recall)
    newcolumn.append(0)
    # Because we're about to add a row.
    confusion = confusion.append(pandas.DataFrame(newrow))
    confusion["recall"] = newcolumn
    pandas.options.display.float_format = '{:20,.2f}'.format
    print()
    print(confusion)




