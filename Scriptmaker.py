# Scriptmaker.py

for i in range(53):
	istr = str(i)
	filepath = "/Users/tunder/Dropbox/pagedata/scripts/java" + istr + ".pbs"
	with open(filepath, mode = "w", encoding = "utf-8") as f:
		f.write("#!/bin/bash\n")
		f.write("#PBS -l walltime=8:00:00\n")
		f.write("#PBS -l nodes=1:ppn=12\n")
		f.write("#PBS -N classifygenres" + istr + "\n")
		f.write("#PBS -q ichass\n")
		f.write("#PBS -m be\n")
		f.write("cd $PBS_O_WORKDIR\n")
		f.write("/projects/ichass/usesofscale/jdk1.8.0_05/bin/java -Xms4096M -Xmx24576M -classpath \".:../weka/weka.jar\" pages/MapPages -model /projects/ichass/usesofscale/models/Model.ser -slice /home/tunder/java/genre/slices/slice" + istr + ".txt -pairtreeroot /projects/ichass/usesofscale/nonserials/ -output /projects/ichass/usesofscale/pagemaps/slice" + istr + "/ -bio -log /home/tunder/java/genre/warninglog" +istr + ".txt")
