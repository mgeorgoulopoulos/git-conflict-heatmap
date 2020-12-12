# (c) 2020 Michael Georgoulopoulos
# This code is licensed under MIT license (see LICENSE for details)
import os
import os.path
import subprocess
import sys

# Settubgs
# ------------------------------------------------------
# Set path of git repo
gitRepoDirectory = 'path/to/git/working/dir';

# Set ratio of conflicts to keep. We will report the top-conflicted files until we reach the ratio of total conflicts specified.
conflictRatioToConsider = 0.25

# How far in the past do you want to look?
since = '2 years 0 months 0 days'

# How many lines away should we start a new cluster?
lineSlackForClustering = 5

originalWorkingDirectory = os.getcwd()
os.chdir(gitRepoDirectory)

# Run the git command
print("Running git log for " + since + ". This may take a while...", flush=True)
command = ['git', 'log', '--cc', '--min-parents=2', '--since="' + since + '"']
result = subprocess.run(command, stdout=subprocess.PIPE, shell=True)

def removeUnicodeCharacters(text):
	return ''.join([i if ord(i) < 128 else ' ' for i in text])

class File:
	def __init__(self, filename):
		self.conflictCount = 0
		self.commits = set()
		self.filename = filename

files = {}

def insertToFiles(filename, commit):
	if not filename in files:
		files[filename] = File(filename)
	files[filename].conflictCount = files[filename].conflictCount + 1
	files[filename].commits.add(commit)

output = result.stdout.decode()
output = removeUnicodeCharacters(output)
for line in output.splitlines():
	if line.startswith('commit '):
		commit = line[7:]
	if line.startswith('+++'):
		# get filename that received a conflict
		filename = line[5:]
		insertToFiles(filename, commit)
		
# Convert to list of files and sort DESC
files = list(files.values())

# Filter out nonexistent files
tmp = []
for file in files:
	if os.path.isfile(gitRepoDirectory + file.filename):
		tmp.append(file)
files = tmp

files.sort(key=lambda x : -x.conflictCount)

# Calculate total conflict count
totalConflictCount = 0;
for file in files:
	totalConflictCount += file.conflictCount

print(len(files), "files,", totalConflictCount, "total conflicts")

# Filter the top conflicted files until we reach a percentage of all the conflicts.
# We are assuming that most of the conflicts end up in a minority of the files. Otherwise all is good (I guess?)
conflictCountToConsider = round(totalConflictCount * conflictRatioToConsider)
tmp = []
conflictsConsidered = 0
for file in files:
	if conflictsConsidered >= conflictCountToConsider:
		break;
	conflictsConsidered += file.conflictCount
	tmp.append(file)
files = tmp

# Print results
print("Selected", len(files), "files, having", conflictsConsidered, "total conflicts (", round(100.0 * conflictsConsidered / totalConflictCount), '% )')

def formatCluster(start, end):
	if start == end:
		return str(start)
	else:
		return str(start) + '-' + str(end)

# In: list of integers which are the line numbers that received conflicts.
# Out: string containing comma-separated clusters of lines "123-456" or single lines "123"
def cluster(lines):
	if len(lines) == 0:
		return ""
	clusterStart = lines[0]
	clusterEnd = lines[0]
	clusters = []
	for l in lines:
		if l > clusterEnd + lineSlackForClustering:
			# Save the old cluster and introduce new
			clusters.append(formatCluster(clusterStart, clusterEnd))
			clusterStart = l		
		# Extend cluster end
		clusterEnd = l
	clusters.append(formatCluster(clusterStart, clusterEnd))
	return ','.join(clusters)
		

# Then, blame all selected files one by one and note the lines that exist in conflicted commits
for file in files:
	command = ['git', 'blame', '-l', file.filename[1:]]
	result = subprocess.run(command, stdout=subprocess.PIPE, shell=True)
	output = result.stdout.decode()
	output = removeUnicodeCharacters(output)
	lineNumber = 1
	linesWithConflicts = []
	for line in output.splitlines():
		commit = line.split(' ')[0]
		if commit in file.commits:
			linesWithConflicts.append(lineNumber)
		lineNumber += 1
	commaSeparatedLines = cluster(linesWithConflicts)
	print(file.filename + "\t" + str(file.conflictCount) + "\t" + commaSeparatedLines)


# Done
os.chdir(originalWorkingDirectory)



