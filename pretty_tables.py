import itertools
import tabulate
possibilities = ["incorrect","correct","empty"]
all_options = itertools.product(possibilities, repeat=2)

table_print_styles = ["plain","simple","grid","fancy_grid","pipe","orgtbl","jira","presto","psql","rst","mediawiki","moinmoin","youtrack","html","latex","latex_raw","latex_booktabs","textile"]

headers = ["username", "password"]

for print_style in table_print_styles:
	print(tabulate(possibilities, headers, tablefmt=print_style))