"""Generate all cobwood plot figures and save them to the scenario plots directory.

Usage
-----

    cd ~/rp/cobwood/scripts
    ipython -i generate_plots.py -- --scenario base_2021

Output files are written to the scenario's plot directory.
"""

import argparse
import os
import matplotlib


from cobwood.gfpmx import GFPMX
from cobwood.plot import (
    bubble_chart,
    grouped_bar,
    parallel_coordinates,
    scatter_matrix,
    sparklines,
    stacked_area,
    trade_balance_matrix,
)

matplotlib.use("Agg")
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--scenario", default="base_2021", help="Scenario name to load")
args = parser.parse_args()

print("Loading model...")
gfpmxb2021 = GFPMX(scenario=args.scenario, rerun=False)


def save(fig, name):
    path = os.path.join(gfpmxb2021.plot_dir, name)
    fig.savefig(path, bbox_inches="tight")
    print(f"  saved {name}")
    matplotlib.pyplot.close(fig)


print("Generating matplotlib plots for sawnwood...")

save(
    bubble_chart(gfpmxb2021["sawn"], year=2021, show_regions=False),
    "bubble_chart_sawn_countries.png",
)
save(
    bubble_chart(gfpmxb2021["sawn"], year=2021, show_regions=True),
    "bubble_chart_sawn_regions.png",
)
save(
    sparklines(gfpmxb2021["sawn"], var="cons", max_countries=30),
    "sparklines_sawn_cons.png",
)
save(
    sparklines(gfpmxb2021["sawn"], var="prod", max_countries=30),
    "sparklines_sawn_prod.png",
)
save(stacked_area(gfpmxb2021["sawn"], var="prod"), "stacked_area_sawn_prod.png")
save(stacked_area(gfpmxb2021["sawn"], var="cons"), "stacked_area_sawn_cons.png")
save(scatter_matrix(gfpmxb2021["sawn"], year=2021), "scatter_matrix_sawn.png")
save(grouped_bar(gfpmxb2021["sawn"], year=2021), "grouped_bar_sawn.png")
save(
    parallel_coordinates(gfpmxb2021["sawn"], year=2021), "parallel_coordinates_sawn.png"
)

print("Generating trade balance matrix (all products)...")
save(trade_balance_matrix(gfpmxb2021, year=2021, top_n=40), "trade_balance_matrix.png")

print(f"\nDone — plots written to {gfpmxb2021.plot_dir}/")
