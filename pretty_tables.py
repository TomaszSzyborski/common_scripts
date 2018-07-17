import itertools
from tabulate import tabulate

possibilities = ["incorrect","correct","empty"]
all_options = list(itertools.product(possibilities, repeat=2))

table_print_styles = ["plain","simple","grid",
					"fancy_grid","pipe","orgtbl",
					"jira","presto","psql",
					"rst","mediawiki","moinmoin",
					"youtrack","html","latex",
					"latex_raw","latex_booktabs","textile"]

headers = ["username", "password"]

for print_style in table_print_styles:
	print(f"Using style: {print_style}")
	print(tabulate(all_options, headers, tablefmt=print_style))