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
# TODO replace this with a function and list comprehension
agg = pandas.concat([roundprodagg, indroundprodagg, fuelprodagg], axis=1)
np.testing.assert_allclose(agg["round"], agg["indround"] + agg["fuel"])

agg_selected = agg.query("year in [2010,2015,2030,2050]").transpose()
# (agg_selected / 1e3).to_csv("/tmp/gfpmxeuagg_selected.csv")
