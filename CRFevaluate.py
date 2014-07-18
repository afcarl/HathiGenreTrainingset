# CRFevaluate.py

import numpy
import pandas

def highestkey(dictionary):
    '''Returns the key with highest value in the
    dictionary provided. Assumes positive numeric values and string
    keys. Does not handle ties in any clever way.'''

    maxval = -1
    maxkey = ""
    for key, value in dictionary.items():
        if value > maxval:
            maxval = value
            maxkey = key

    return maxkey

def defaultbelowthreshold(predicted, default, threshold):
	'''Returns the key with highest value in dict "predicted",
	as long as it's above a numeric "threshold." Otherwise
	it returns "default," which we expect to be a key in the
	dictionary.
	'''
	maxval = threshold
	maxkey = default

	for key, value in predicted.items():

		if value > maxval:
			maxval = value
			maxkey = key

	return maxkey

def defaultwithsafeguard(predicted, default, threshold):
	'''Returns the key with highest value in dict "predicted",
	as long as it's above a numeric "threshold." Otherwise
	it returns "default," which we expect to be a key in the
	dictionary.
	'''
	maxval = threshold
	maxkey = default
	safeguard = 1 - threshold

	for key, value in predicted.items():

		if value > maxval and predicted[default] < safeguard:
			maxval = value
			maxkey = key

	return maxkey

def decide(predicted, classes, method):

	if method < 0 and method > -0.02:
		return highestkey(predicted)
	if method < - 0.015:
		return "model"
	else:
		return defaultwithsafeguard(predicted, "model", method)

def printconfusionmatrix(predicted):
	confusion = pandas.DataFrame(predicted)

	newrow = dict()
	newcolumn = list()
	columngenres = [x for x in confusion.columns]

	accurate = 0
	total = 0
	for genre in columngenres:
		accurate += confusion.loc[genre, genre]
		total += confusion[genre].sum()

	print()
	print("Microaveraged: " + str(accurate/total))
	microaveraged = accurate/total

	for genre in columngenres:
		precision = (confusion.loc[genre, genre] / confusion[genre].sum()) * 100
		newrow[genre] = {'precision': precision}
		recall = (confusion.loc[genre, genre] / confusion.loc[genre].sum()) * 100
		newcolumn.append(recall)
	newcolumn.append(0)
	# Because we're about to add a row.
	confusion = confusion.append(pandas.DataFrame(newrow))
	confusion["recall"] = newcolumn
	pandas.options.display.float_format = '{:10.1f}'.format
	print()
	print(confusion)

	for genre in columngenres:
		precision = confusion.loc["precision", genre]
		recall = confusion.loc[genre, "recall"]
		F1 = 2 * ((precision * recall) / (precision + recall))
		print(genre + " \tF1 = " + str(F1))

	return microaveraged

def getmatrix(setting):
	predictedbyactual = dict()
	for aclass in classes:
		predictedbyactual[aclass] = dict()
		for anotherclass in classes:
			predictedbyactual[aclass][anotherclass] = 0

	for line in filelines:
		line = line.rstrip()
		fields = line.split("\t")
		actual = fields[0]
		predicted = dict()
		for i in range(0,4):
			predicted[classes[i]] = float(fields[i+1])
		prediction = decide(predicted, classes, method = setting)
		predictedbyactual[prediction][actual] += 1

	microavg = printconfusionmatrix(predictedbyactual)
	return microavg

# def main():
with open("/Volumes/TARDIS/output/forests/probabilities.tsv", encoding="utf-8") as f:
	filelines = f.readlines()

classes = ["model", "runnerup", "prev", "next"]

bestresult = 0
bestsetting = 0
for i in range (50, 100, 1):

	setting = i / 100
	print("\nSetting:")
	print(setting)
	print('\n')
	result = getmatrix(setting)
	if result > bestresult:
		bestsetting = setting
		bestresult = result

print(bestsetting, bestresult)

# if __name__ == "__main__":
# 	main()

