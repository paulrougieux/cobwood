""" The purpose of this script is to compute the percentage increase of roundwood harvest by 2050

Run this script at the command line with:

    ipython -i ~/repos/cobwood/scripts/explore_gfpmx_data.py


- Compute the aggregate for EU countries of production and consumption.
- Compute the percentage change between any given year.

"""

import numpy as np
import pandas
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from biotrade.faostat import faostat
from cobwood.gfpmx_data import GFPMXData
import cobwood

gfpmx_data = GFPMXData(data_dir="gfpmx_8_6_2021")

# Path to Valerio's EU Net Annual Increment data
eu_cbm_explore_path = cobwood.data_dir.parent / "eu_cbm" / "eu_cbm_explore"
nai_path = eu_cbm_explore_path / "scenarios" / "avitabile_nai"

# Load GFTMx data
round_ = gfpmx_data.get_country_rows("round")
fuel = gfpmx_data.get_country_rows("fuel")
indround = gfpmx_data.get_country_rows("indround")
area = gfpmx_data.get_sheet_long("area")
stock = gfpmx_data.get_sheet_long("stock")

# Load NAI data and compute total yearly increment
nai_eu = pandas.read_csv(nai_path / "avitabile_2023_nai_eu.csv")
nai_eu["tot_nai_thousand_m3_ob"] = nai_eu["nai_ha"] * nai_eu["forest_area_kha"]
nai_eu["faws_nai_thousand_m3_ob"] = nai_eu["nai_ha"] * nai_eu["faws_area_kha"]
# Net Annual Increment in Forests Availaable for Wood Supply in thousand m3 under bark
nai_eu["faws_nai_thousand_m3_ub"] = nai_eu["nai_ha"] * nai_eu["faws_area_kha"] / 1.12

# Select EU countries
eucountries = faostat.country_groups.eu_country_names + ["Czech Republic"]
roundeu = round_.query("country in @eucountries")
indroundeu = indround.query("country in @eucountries")
fueleu = fuel.query("country in @eucountries")

# Check number of countries
print(set(eucountries) - set(indroundeu.reset_index().country.unique()))
print(indroundeu.reset_index().country.unique())


def print_increase_in_production(df, var, start, end):
    """Print the difference in production between the start and the end date"""
    df_change = df.loc[end, var].sum() / df.loc[start, var].sum()
    print(
        f"Increase in {df['faostat_name'].unique()} {var} between {start} and {end}:",
        round((df_change - 1) * 100),
        "%",
        f"from {round(df.loc[start, var].sum()/1e3)}",
        f"to {round(df.loc[end, var].sum()/1e3)} million m3",
    )


print_increase_in_production(roundeu, "prod", 2020, 2050)
print_increase_in_production(indroundeu, "prod", 2020, 2050)
print_increase_in_production(fueleu, "prod", 2020, 2050)

print_increase_in_production(fueleu, "prod", 2022, 2050)
print_increase_in_production(indroundeu, "prod", 2022, 2050)

print_increase_in_production(indroundeu, "cons", 2020, 2050)
print_increase_in_production(fueleu, "cons", 2020, 2050)


# Export summary tables to a spreadsheet
roundprodagg = roundeu.groupby("year")["prod"].agg(sum).rename("round")
indroundprodagg = indroundeu.groupby("year")["prod"].agg(sum).rename("indround")
fuelprodagg = fueleu.groupby("year")["prod"].agg(sum).rename("fuel")


def aggregate_eu(sheet_name, variable):
    """Load and aggregate the given variable for EU countries
    Example use:
        >>> round_prod_agg = aggregate_eu("roundprod", "prod")
        >>> stock_agg = aggregate_eu("stock", "stock")
    """
    df = gfpmx_data.get_sheet_long(sheet_name).query("country in @eucountries")
    df_agg = df.groupby("year")[variable].agg(sum).rename(sheet_name)
    return df_agg


stock_agg = aggregate_eu("stock", "stock")
area_agg = aggregate_eu("area", "area")
round_prod_agg = aggregate_eu("roundprod", "prod")
sheet_and_variable = [
    ("area", "area"),
    ("stock", "stock"),
    ("roundprod", "prod"),
    ("indroundprod", "prod"),
    ("fuelprod", "prod"),
]
agg_eu = pandas.concat(
    [aggregate_eu(*sheet_var) for sheet_var in sheet_and_variable], axis=1
)

np.testing.assert_allclose(
    agg_eu["roundprod"], agg_eu["indroundprod"] + agg_eu["fuelprod"]
)
# Note: Time series start in 1992
agg_selected = agg_eu.query("year in [1992,2000,2010,2020,2030,2050,2070]").transpose()
# Divide by 1000 and write to a csv file
# Forest area in 1000 ha -> million ha
# Stock in Million M3 -> billion m3
# Harvest in 1000 m3 -> million m3
(agg_selected / 1e3).round().to_csv("/tmp/gfpmxeuagg_selected.csv")

# Add Net Annual Increment to the harvest data
# Set the index so that it is passed on as an index
naihar_eu = agg_eu.merge(nai_eu.set_index("year"), on="year", how="left")
naihar_eu["faws_nai_thousand_m3_ub"] = naihar_eu["faws_nai_thousand_m3_ub"].interpolate(
    method="linear", limit_area="inside"
)

# Plot EU harvest projection
selector = agg_eu.index <= 2050
cols = ["roundprod", "indroundprod", "fuelprod", "nai_thousand_m3"]
cols_plot = {
    "roundprod": "Total Roundwood removals",
    "indroundprod": "Industrial Roundwood",
    "fuelprod": "Fuel wood",
    "faws_nai_thousand_m3_ub": "Net Annual Increment (FAWS, UB)",
}
(
    (naihar_eu.loc[selector, cols_plot.keys()] / 1e3)
    .rename(columns=cols_plot)
    .plot(
        title="GFPMx EU 27 harvest projections in the SSP2 scenario",
        ylabel="Million m3",
        colormap=ListedColormap(["black", "orange", "red", "green"]),
    )
)
# plt.show()
plt.savefig("/tmp/gfpmx_eu_havest.png")


# Compute production per capita
naihar_eu_agg = naihar_eu.groupby("year").sum()

# Population The EU population is projected to increase from 446.7 million in
# 2022 and peak at 453.3 million in 2026 (+1.5 %), then gradually decrease to
# 447.9 million in 2050

# Production is in 1000 m3
print(
    "EU roundwood harvest per person in 2020:",
    round(naihar_eu_agg.loc[2020, "roundprod"] / 446.7e3, 1),
    "m3",
)
print(
    "EU roundwood harvest per person in 2020:",
    round(naihar_eu_agg.loc[2050, "roundprod"] / 447.9e3, 1),
    "m3",
)
print(
    "EU faws_nai_thousand_m3_ub harvest per person in 2020:",
    round(naihar_eu_agg.loc[2020, "faws_nai_thousand_m3_ub"] / 446.7e3, 1),
    "m3",
)
