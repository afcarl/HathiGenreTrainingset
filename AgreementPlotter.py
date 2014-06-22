# plotter

import matplotlib.pyplot as plt
import SonicScrewdriver as utils
import pandas as pd
from scipy.stats.stats import pearsonr

indices, columns, agreement = utils.readtsv("/Users/tunder/Dropbox/pagedata/interrater/HumanAgreement.tsv")

indices2, columns2, confidence = utils.readtsv("/Users/tunder/Dropbox/pagedata/interrater/MachineConfidence.tsv")

for idx in indices:
	if idx not in indices2:
		print(idx + " is missing.")

makeframe = dict()

makeframe["human-agreement"] = agreement["agreement"]
makeframe["machine-confidence"] = confidence["accuracy"]

df = pd.DataFrame(makeframe, dtype="float")
df = df.dropna()

print(str(pearsonr(df["human-agreement"], df["machine-confidence"])))

plt.plot(df["human-agreement"], df["machine-confidence"], "r.")
plt.xlabel("Human agreement")
plt.ylabel("Machine confidence")
plt.axis([0,1,0,1])
plt.show()

