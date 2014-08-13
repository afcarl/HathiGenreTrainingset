import os

indir = "/Users/tunder/Dropbox/pagedata/production/oldfiles/"
filelist = os.listdir(indir)

for filename in filelist:
	with open(indir + filename, encoding = "utf-8") as f:
		fl = f.readlines()

	for line in fl:
		fields = line.split('\t')
		pg = int(fields[0])
		if pg < 0:
			print(line)
