#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A script to compute GFPMX demand recursively in a time loop

Run this file with:

     ipython -i ~/rp/gftmx/scripts/compute_demand.py

"""

from gftmx.gfpmx_data import gfpmx_data
# Load sawnwood data
swd = gfpmx_data.join_sheets("sawn", ["gdp"])
swd.head()

# Number of years and number of countries
years = swd.index.to_frame()["year"].unique()
countries = swd.index.to_frame()["country"].unique()
print("Years:", years)
print("Countries:", countries)
print("Number of lines in the swd data frame:", len(swd))
print("Number of years time the number of countries: ",
      len(years), "*", len(countries), "=", len(years) * len(countries))

# swd.to_csv("/tmp/swd.csv") # Open with gx


# Use both indexes again
# Doesn't work because the following has an NA value
## swd.loc[t-1, "price"].pow(swd.loc[t, "cons_price_elasticity"])
swd = swd.copy()
def shift_index(previous):
    """Update the index of a lagged variable
    To store last year's prices in a "price_lag" column at year t.
    We first need to update the index from year t-1 to year t.
    Otherwise assignation of .loc[[t], "price_lag"] would contain NA values.
    """
    previous = previous.reset_index()
    previous["year"] = previous["year"] + 1
    previous = previous.set_index(["year", "country"])["price"]
    return previous
def compute_demand(df):
    """GFPMX demand equation"""
    return (df["cons_constant"]
            * df["price_lag"].pow(df["cons_price_elasticity"])
            * df["gdp"].pow(df["cons_gdp_elasticity"])
           )
# Start one year after the base year so price_{t-1} exists already
for t in range(gfpmx_data.base_year + 1, years.max() + 1):
    swd.loc[[t], "price_lag"] = shift_index(swd.loc[[t-1], "price"])
    swd.loc[[t], "cons2"] = compute_demand(swd.loc[[t]])
swd['comp_prop'] = swd.cons2 / swd.cons - 1
print(swd["comp_prop"].abs().max())
print(swd.query("year >= 2019")[["price_lag", "gdp", "cons", "cons2"]])


# # Nested loop version.
# # This version is abandoned and kept as a comment here.
# swd2 = swd.copy()
# for t in range(gfpmx_data.base_year + 1, years.max()+1):
#     for c in countries:
#         # Consumption
#         swd2.loc[(t,c), "cons2"] = (swd2.loc[(t, c), "cons_constant"]
#                                    * pow(swd2.loc[(t-1, c), "price"],
#                                          swd2.loc[(t, c), "cons_price_elasticity"])
#                                    * pow(swd2.loc[(t, c), "gdp"],
#                                          swd2.loc[(t, c), "cons_gdp_elasticity"])
#                                   )
# swd2['comp_prop'] = swd2.cons2 / swd2.cons -1
# print(swd2["comp_prop"].abs().max())
