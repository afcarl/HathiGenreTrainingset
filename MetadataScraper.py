import urllib.request, codecs
import FileUtils
import json

outpath = "/Users/tunder/Dropbox/pagedata/metascrape/"

# The indented section below is a function that gets called by the main program.
# Skip over this for now and start reading at MAIN below.

def getsource(URL):
    """This actually gets the source text for the web page."""
    Response = urllib.request.urlopen(URL)
    ByteList = Response.readlines()
    StringVersion = ""
    for Line in ByteList:
        StringVersion = StringVersion + Line.decode('utf-8')
    return(StringVersion)

def getnames(text):
    names = list()

    males = text.split('<arr name="htrc_genderMale">')
    if len(males) > 1:
        name = males[1].split("</str>")[0]
        name = name.replace("<str>", "")
        names.append((name, "m"))

    females = text.split('<arr name="htrc_genderFemale">')
    if len(females) > 1:
        name = females[1].split("</str>")[0]
        name = name.replace("<str>", "")
        names.append((name, "f"))

    return(names)

## We start by loading the list of volumes for which we need a
## Library of Congress Call Number.

import SonicScrewdriver as utils

rowindices, columns, metadata = utils.readtsv("/Users/tunder/Dropbox/PythonScripts/hathimeta/ExtractedMetadata.tsv")

neededoclcs = list()
reversemap = dict()

for idx in rowindices:
    if metadata["LOCnum"][idx] == "<blank>" and metadata["OCLC"][idx] != "<blank>":
        oclc = metadata["OCLC"][idx]
        neededoclcs.append(oclc)
        reversemap[oclc] = idx

counter = 0
metacounter = 0
lccndict = dict()
responsedict = dict()

for oclc in neededoclcs:
    counter += 1

    url = "http://xisbn.worldcat.org/webservices/xid/oclcnum/" + oclc + "?wskey=nZn3cw2Lvndx06mHV9P8tStmwZEb4BWg7Uh1oeDfR9U1GYVaHjt0C41zk1RWHGzesu4f6gwm1403jgpSmethod=getMetadata&format=json&fl=*"

    try:
        text = getsource(url)
        j = json.loads(text)
        newjson = dict()
        newjson[oclc] = j["list"]
        responsedict[oclc] = json.dumps(newjson)

        for valuedictionary in j["list"]:
            if "lccn" in valuedictionary:
                lccn = valuedictionary["lccn"]
                lccndict[oclc] = lccn
                print(str(counter) + " : " + str(lccn))

    except KeyboardInterrupt:
        sys.exit("Stopped by user.")
    except IOError as err:
        print(err)
        responsedict[oclc] = "{}"
    except KeyError as err:
        print(err)
        responsedict[oclc] = "{}"
    except:
       responsedict[oclc] = "{}"
       print("Unknown fail.")



    if counter > 100:
        print(counter)
        outfile = outpath + "batch" + str(metacounter) + ".json"
        with open(outfile, mode='w', encoding='utf-8') as f:
            for key, jsonstring in responsedict.items():

                jsonstring = jsonstring.replace("\n", "")
                f.write(jsonstring + "\n")
        counter = 0
        metacounter += 1
        responsedict = dict()
        outfile = outpath + "alccntable.tsv"
        with open(outfile, mode='a', encoding='utf-8') as f:
            for key, value in lccndict.items():
                outline = str(key) + '\t' + str(value) + '\n'
                f.write(outline)
        lccndict = dict()


