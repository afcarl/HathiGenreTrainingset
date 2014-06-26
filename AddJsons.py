import json
import sys, os

jdir = "/Users/tunder/Dropbox/pagedata/jsons/"
dirlist = os.listdir(jdir)

sumjson = dict()
tlword = "top_level_word_graph"
tlvol = "top_level_volume_graph"
sumjson[tlword] = dict()
sumjson[tlvol] = dict()

sumjson[tlword]["drama"] = [0] * 200
sumjson[tlword]["paratext"] = [0] * 200
sumjson[tlword]["fiction"] = [0] * 200
sumjson[tlword]["poetry"] = [0] * 200
sumjson[tlword]["nonfiction"] = [0] * 200

sumjson[tlvol]["drama"] = [0] * 200
sumjson[tlvol]["fiction"] = [0] * 200
sumjson[tlvol]["nonfiction"] = [0] * 200
sumjson[tlvol]["mixed"] = [0] * 200
sumjson[tlvol]["poetry"] = [0] * 200

def addtwo(list1, list2):
	assert len(list1) == len(list2)
	list3 = list()
	for i in range(len(list1)):
		list3.append(int(list1[i]) + int(list2[i]))
	return list3

for filename in dirlist:
	if not filename.endswith(".json"):
		continue

	filepath = os.path.join(jdir, filename)
	with open(filepath, mode="r", encoding="utf-8") as f:
		jsonstring = f.read()
	jobject = json.loads(jsonstring)

	word = jobject[tlword]
	sumjson[tlword]["drama"] = addtwo(sumjson[tlword]["drama"], word["drama"])
	sumjson[tlword]["paratext"] = addtwo(sumjson[tlword]["paratext"], word["ads"])
	sumjson[tlword]["paratext"] = addtwo(sumjson[tlword]["paratext"], word["front"])
	sumjson[tlword]["paratext"] = addtwo(sumjson[tlword]["paratext"], word["back"])
	sumjson[tlword]["nonfiction"] = addtwo(sumjson[tlword]["nonfiction"], word["biography"])
	sumjson[tlword]["fiction"] = addtwo(sumjson[tlword]["fiction"], word["fiction"])
	sumjson[tlword]["poetry"] = addtwo(sumjson[tlword]["poetry"], word["poetry"])
	sumjson[tlword]["nonfiction"] = addtwo(sumjson[tlword]["nonfiction"], word["nonfiction"])

	sumjson[tlword]["years"] = word["years"]
	sumjson[tlword]["genres"] = word["genres"]

	vol = jobject[tlvol]

	sumjson[tlvol]["drama"] = addtwo(sumjson[tlvol]["drama"], vol["drama"])
	sumjson[tlvol]["fiction"] = addtwo(sumjson[tlvol]["fiction"], vol["fiction"])
	sumjson[tlvol]["nonfiction"] = addtwo(sumjson[tlvol]["nonfiction"], vol["nonfiction"])
	sumjson[tlvol]["mixed"] = addtwo(sumjson[tlvol]["mixed"], vol["mixed"])
	sumjson[tlvol]["poetry"] = addtwo(sumjson[tlvol]["poetry"], vol["poetry"])

	sumjson[tlvol]["years"] = vol["years"]
	sumjson[tlvol]["genres"] = vol["genres"]

jsonstring = json.dumps(sumjson)
with open(jdir + "realdata.json", mode="w", encoding="utf-8") as f:
	f.write(jsonstring)


