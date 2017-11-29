#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import requests as r
import pandas as pd
"""
Requirements:
Print answers for following questions:
1. How many total open issues are there across all repositories?
2. Sort the repositories by date updated in descending order.
3. Which repository has the most watchers?
"""

def print_repo_name_and_url(list_of_dicts):
	"""
	Print list of records by full_name and url

    Positional arguments:
    list_of_dicts -- list of dictionaries contaning repositories' full_name and url
	
	Keys to dictionaries are "full_name", and "url"
	"""
	_separator = "-"*80
	for d in list_of_dicts:
		print("Name of repository: {}\n URL of repository: {}\n{}"
			.format(d["full_name"],
				d["url"],
				_separator))

# Get List of repositories
username = "tomaszszyborski"
repositories = pd.read_json(
	json.dumps(
		r.get("https://api.github.com/users/{}/repos".format(username))
	.json()))

# Answer for question nr 1
print("1. How many total open issues are there across all repositories?")
print("Answer:\nTotal open issues: {}".format(repositories["open_issues_count"].sum()))

# Answer for question nr 2
sorted_repos = repositories.sort_values(by="updated_at", ascending=False)
answer_2 = sorted_repos.loc[:,["full_name","url"]].to_dict(orient="records")

print("2. Sort the repositories by date updated in descending order.")
print("Answer:")
print_repo_name_and_url(answer_2)

# Answer for question nr 3
answer_3 = repositories[
		repositories["watchers_count"]
		== repositories["watchers_count"].max()].loc[
		:,["full_name","url"]].to_dict(orient="records")

print("3. Which repository has the most watchers?")
print("Answer:")
print_repo_name_and_url(answer_3)
