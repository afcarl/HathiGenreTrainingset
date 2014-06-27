# make bubble plot

human = c(98.9, 88.4, 94.1, 92.7, 91.2)
machine = c(94.9, 94.4, 95.6, 75.6, 90.3)
size = c(1, 5, 30, 1, 2)
labels = c("drama", "fiction", "nonfiction", "paratext", "poetry")
data = data.frame(genre = labels, human = human, machine=machine, size=size)
library(ggplot2)
q <- ggplot(data, aes(x=machine, y=human))
q <- q + geom_point(aes(size = sqrt(size/pi)), pch = 21, show_guide = FALSE) + 
  scale_size_continuous(range = c(5,80)) +
  aes(fill = genre) + scale_fill_manual(values = gColors) + 
  annotate("text", x=75.6, y= 93.5,label = "paratext", size = 7) + 
  annotate("text", x=94.9, y= 98.2,label = "drama", size = 7) + 
  annotate("text", x=95.5, y= 94.1,label = "nonfiction", size =7) + 
  annotate("text", x=94.4, y= 89.9,label = "fiction", size=7) + 
  annotate("text", x=90.3, y= 92.2, label = "poetry", size=7) + 
  scale_x_continuous(name = "\nalgorithmic accuracy", limits = c(75,100)) + 
  scale_y_continuous(name = "human agreement\n", limits = c(87.5,100)) + 
  theme(text = element_text(size = 16)) +  
  theme(title = element_text(size = 16))