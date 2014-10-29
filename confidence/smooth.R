# smooth precision-recall curves
library(zoo)
# we need the locf function
conf80 <- read.csv('/Users/tunder/output/confidence80.csv')
conf80 <- na.locf(conf80)
for (i in 1:4) {
  conf80[[i]] <- lowess(conf80[[i]], f = .3)$y
}

write.csv(conf80, file = '/Users/tunder/Dropbox/PythonScripts/training/alldata/confidence/smoothed.csv', row.names = FALSE)