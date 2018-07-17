import itertools
from tabulate import tabulate

possibilities = ["incorrect","correct","empty"]
headers = ["username", "password"]

all_options = list(itertools.product(possibilities, repeat=2))
all_options = [list(tup) for tup in all_options]

table_print_styles = ["plain","simple","grid",
					"fancy_grid","pipe","orgtbl",
					"jira","presto","psql",
					"rst","mediawiki","moinmoin",
					"youtrack","html","latex",
					"latex_raw","latex_booktabs","textile"]

final_options = []
for username in ("Admin", "User"):
	for index, _ in enumerate(all_options):
		final_options.append([username] + all_options[index])

for print_style in table_print_styles:
	print(f"Using style: {print_style}")
	print(tabulate(final_options, headers, tablefmt=print_style))