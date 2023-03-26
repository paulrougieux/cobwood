""" The purpose of this script is to compute the percentage increase of roundwood harvest by 2050

Run this script at the command line with:

    ipython -i ~/repos/gftmx/scripts/explore_gfpmx_data.py


- Compute the aggregate for EU countries of production and consumption.
- Compute the percentage change between any given year.

"""
import numpy as np
import pandas
from biotrade.faostat import faostat
from gftmx.gfpmx_data import gfpmx_data

round_ = gfpmx_data.get_country_rows("round")
fuel = gfpmx_data.get_country_rows("fuel")
indround = gfpmx_data.get_country_rows("indround")
area = gfpmx_data.get_sheet_long("area")
stock = gfpmx_data.get_sheet_long("stock")


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


def agg_eu(sheet_name, variable):
    """Load and aggregate the given variable for EU countries
    Example use:
        >>> round_prod_agg = agg_eu("roundprod", "prod")
        >>> stock_agg = agg_eu("stock", "stock")
    """
    df = gfpmx_data.get_sheet_long(sheet_name).query("country in @eucountries")
    df_agg = df.groupby("year")[variable].agg(sum).rename(sheet_name)
    return df_agg


stock_agg = agg_eu("stock", "stock")
area_agg = agg_eu("area", "area")
round_prod_agg = agg_eu("roundprod", "prod")
sheet_and_variable = [
    ("area", "area"),
    ("stock", "stock"),
    ("roundprod", "prod"),
    ("indroundprod", "prod"),
    ("fuelprod", "prod"),
]
agg_eu = pandas.concat([agg_eu(*sheet_var) for sheet_var in sheet_and_variable], axis=1)

np.testing.assert_allclose(
    agg_eu["roundprod"], agg_eu["indroundprod"] + agg_eu["fuelprod"]
)
agg_selected = agg_eu.query("year in [2010,2015,2030,2050]").transpose()
# Divide by 1000 and write to a csv file
# Forest area in 1000 ha -> million ha
# Stock in Million M3 -> billion m3
# Harvest in 1000 m3 -> million m3
# (agg_selected / 1e3).to_csv("/tmp/gfpmxeuagg_selected.csv")
