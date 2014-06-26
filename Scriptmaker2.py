# Scriptmaker.py

for i in range(26, 52, 6):
	istr = str(i)
	filepath = "/Users/tunder/Dropbox/pagedata/jsons/collate" + istr + ".pbs"
	with open(filepath, mode = "w", encoding = "utf-8") as f:
		f.write("#!/bin/bash\n")
		f.write("#PBS -l walltime=8:00:00\n")
		f.write("#PBS -l nodes=1:ppn=12\n")
		f.write("#PBS -N jsonsummary" + istr + "\n")
		f.write("#PBS -q ichass\n")
		f.write("#PBS -m be\n")
		f.write("cd $PBS_O_WORKDIR\n")
		f.write("/projects/ichass/usesofscale/jdk1.8.0_05/bin/java -Xms4096M -Xmx24576M collate/Collate -slice /projects/ichass/usesofscale/pagemaps/slice -startint " + istr + " -pairtreeroot /projects/ichass/usesofscale/nonserials/ -metadata /projects/ichass/usesofscale/hathimeta/ExtractedMetadata.tsv -output /projects/ichass/usesofscale/jsons/ -log /projects/ichass/usesofscale/jsons/warninglog" + istr + ".txt")
