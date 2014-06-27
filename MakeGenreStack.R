# Making a stack graph from munged JSON data

stack <- read.table("/Users/tunder/Dropbox/pagedata/jsons/forR.tsv", sep = "\t", header = TRUE, colClasses = "numeric")
# for (i in 2:6) {
#   stack[ , i] = smooth(stack[ , i])
# }

df <- data.frame(x = rep(stack$date, 5), y = c(stack$poetry, stack$paratext, stack$nonfiction, stack$drama, stack$fiction), genre = c(rep(" poetry", 200), rep(" paratext", 200), rep(" nonfiction", 200), rep(" drama", 200), rep(" fiction", 200)))
chromatic = c("mediumorchid2", "navy", "lightsteelblue", "oldlace", "mediumseagreen")
p <-ggplot(df, aes(x=x, y=y, group = genre, colour = genre)) + scale_colour_manual(guide=FALSE, values = chromatic)
p <- p + geom_area(aes(colour=genre, fill = genre, name = "genre\n"), position = 'stack') + scale_fill_manual(values = chromatic, name = "genre\n", guide = guide_legend(keyheight=2))
p <- p + scale_x_continuous("") + scale_y_continuous("percent of words in genre\n") +
  theme(text = element_text(size = 30)) +  theme(title = element_text(size = 30))
print(p)