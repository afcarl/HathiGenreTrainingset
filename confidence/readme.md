The important scripts here are logisticmodel.py and smooth.R. These generate a meta-model characterizing our confidence in the predictions made about volumes, which is used to create metadata that accompanies the predictions for each volume.

Older scripts (logitconfidence and modelconfidence.py) represent discarded branches that used different modeling strategies. A straightforward logistic regression on binarized data turned out to work best.
