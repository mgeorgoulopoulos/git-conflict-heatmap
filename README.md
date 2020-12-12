# Overview

git-conflict-heatmap is a simple python script that attempts to identify which files in your git repository are responsible for the most conflicts.

Conflicts are both risky and time-consuming so identifying files that tend to attract conflicts can be useful.

# Method

Here is how it works:

 - List all commits with merges:

```
git log  --cc --min-parents=2
```

 - Filter out the lines that start with '+++' and keep the filename that received a conflict and the SHA-1 of the commit.
 - Drop files that don't exist anymore.
 - Sort the files according to how many conflicts each file received.
 - Keep the N first files which account for 25% of all conflicts. Usually, just a handful of files attract the most conflicts and thus deserve further attention.
 - Attempt to find specific lines in the files that resulted from conflicts.

The final step is not that refined. It just does a git-blame and marks all the lines that happened to be touched by commits that are known to have had conflicts. So it will miss past conflicts (overwritten by subsequent commits) and also it will report some lines that were automatically merged but not conflicted. This is just provided as a guide to begin your search, identify which blocks of code attract conflicts and try to figure out how to avoid them.

# Usage

Edit the py file and change the following settings:

```{python}
# Set path of git repo
gitRepoDirectory = '/path/to/working/dir';

# Set ratio of conflicts to keep. We will report the top-conflicted files until we reach the ratio of total conflicts specified.
conflictRatioToConsider = 0.25

# How far in the past do you want to look?
since = '2 years 0 months 0 days'

# How many lines away should we start a new cluster?
lineSlackForClustering = 5
```

The last parameter is to facilitate clustering of the returned lines. Some files may have a lot of candidate lines found, so we batch nearby lines together in "from-to" ranges. This setting specifies how far are we allowed to jump while creating a new range.

# Example
I used a random git repository I found on GitHub "trending projects" for this test:  [nlohmann/json](https://github.com/nlohmann/json).
Here is the output:
```
$ python git-conflict-heatmap.py
Running git log for 2 years 0 months 0 days. This may take a while...
19 files, 31 total conflicts
Selected 2 files, having 8 total conflicts ( 26 % )
/single_include/nlohmann/json.hpp       4       2369-2370
/include/nlohmann/json.hpp      4       1229-1232
```

So, it found two instances of json.hpp, which is expected. A central header of a library would attract the most conflicts.

The format of the output is TAB-separated, so it can be copied to a speadsheet. There are 3 columns: filename, conflict count, line ranges that possibly received conflicts.

This last field is comma-separated and the elements joined by comma can be either integers (single lines) or ranges formatted as: "from-to" pairs, with a minus sign in-between.
