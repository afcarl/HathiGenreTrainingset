# Gather models into an ensemble.
# Ensemble.py

import os
import numpy as np
import pandas as pd
from scipy.stats.stats import pearsonr
import SonicScrewdriver as utils
import MetadataCascades as cascades
import Coalescer
from math import log
import statsmodels.api as sm
import json
import ConfusionMatrix
import random

def pairtreelabel(htid):
    ''' Given a clean htid, returns a dirty one that will match
    the metadata table.'''

    if '+' in htid or '=' in htid:
        htid = htid.replace('+',':')
        htid = htid.replace('=','/')

    return htid

infolder = "ensemble0"

predictroot = "/Volumes/TARDIS/output/"
firstdir = predictroot + infolder + "/"
predictfiles = os.listdir(firstdir)

validfiles = list()

for filename in predictfiles:
	if filename.endswith(".predict"):
		validfiles.append(filename)

otherdir = predictroot + "ensemble2" + "/"

for filename in validfiles:
	with open(firstdir + filename, encoding = "utf-8") as f:
		fl1 = f.readlines()
	with open(otherdir + filename, encoding = "utf-8") as f:
		fl2 = f.readlines()

	for idx, line in enumerate(fl1):
		jsonobj = json.loads(line)
		otherobj = json.loads(fl2[idx])
		for key, value in jsonobj.items():
			if otherobj[key] != value:
				print(str(idx) + key)
				print(value)
				print(otherobj[key])
				print("-------------")



