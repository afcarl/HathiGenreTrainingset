#compare vocabularies

import glob

# vocabs = glob.glob("*vocab*")

vocabs = ['enlargedvocabulary.txt', 'newmethodvocabulary.txt', 'biggestvocabulary.txt', 'reducedvocabulary2.txt']

print(vocabs)

vocadict = dict()
vocasize = list()

for filename in vocabs:
	with open(filename, encoding="utf-8") as f:
		fl = f.readlines()
	thisset = set([x.strip() for x in fl])
	vocadict[filename] = thisset
	vocasize.append((len(thisset), filename))

sortedvocabs = sorted(vocasize)
lastset = set()
for atuple in sortedvocabs:
	size, filename = atuple
	thisset = vocadict[filename]
	print(filename)
	print(size)
	print(lastset - thisset)
	lastset = thisset
	print("----------------")


