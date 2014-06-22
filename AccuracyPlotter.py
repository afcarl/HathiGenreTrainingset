# plotter

import matplotlib.pyplot as plt
import SonicScrewdriver as utils
import pandas as pd
from scipy.stats.stats import pearsonr

indices, columns, agreement = utils.readtsv("/Users/tunder/Dropbox/pagedata/interrater/HumanAgreement.tsv")

indices2, columns2, confidence = utils.readtsv("/Users/tunder/Dropbox/pagedata/interrater/ActualAccuracies.tsv")

for idx in indices:
	if idx not in indices2:
		print(idx + " is missing.")

makeframe = dict()

makeframe["human-agreement"] = agreement["agreement"]
makeframe["machine-accuracy"] = confidence["accuracy"]

df = pd.DataFrame(makeframe, dtype="float")
df = df.dropna()

print(str(pearsonr(df["human-agreement"], df["machine-accuracy"])))

plt.plot(df["human-agreement"], df["machine-accuracy"], "r.")
plt.xlabel("Human agreement")
plt.ylabel("Machine accuracy")
plt.axis([0,1.02,0,1.02])
plt.show()

