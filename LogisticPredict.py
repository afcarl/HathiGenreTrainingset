# LogisticPredict.py

import numpy as np
import pandas as pd
import math

def logit(a):
	return 1 / (1 + math.exp(-a))

def logitpredict(params, pandaframe):
	'''Expects the first parameter to be a pandas series
	produced by the "params" attribute of a logistic model, and the
	second parameter to be a data frame with columns that align
	with the indexes to the series.'''

	rowcount = pandaframe.shape[0]
	assert len(params) == pandaframe.shape[1]
	# column count should equal length of params

	columns = [x for x in params.index]
	results = np.zeros(rowcount)

	for idx in columns:
		print(idx)
		results += pandaframe[idx] * params[idx]

	for i in range(rowcount):
		results[i] = logit(results[i])

	return results
