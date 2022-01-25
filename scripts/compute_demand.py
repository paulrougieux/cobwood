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
n_years = swd.index.to_frame().year.unique()
n_countries = swd.index.to_frame().country.unique()
print("Years:", n_years)
print("Countries:", n_countries)
print("Number of lines in the swd data frame:", len(swd))
print("Number of years time the number of countries: ",
      len(n_years), "*", len(n_countries), "=", len(n_years) * len(n_countries))

# swd.to_csv("/tmp/swd.csv") # Open with gx

# Compute the consumption
years = swd.index.to_frame()["year"].unique()
countries = swd.index.to_frame()["country"].unique()

# Start one year after the base year so price_{t-1} exists already
for t in range(gfpmx_data.base_year + 1, years.max()+1):
    # TODO: replace this loop by vectorized operations using only the index on years
    for c in countries:
        # Consumption
        swd.loc[(t,c), "cons2"] = (swd.loc[(t, c), "cons_constant"]
                                   * pow(swd.loc[(t-1, c), "price"],
                                         swd.loc[(t, c), "cons_price_elasticity"])
                                   * pow(swd.loc[(t, c), "gdp"],
                                         swd.loc[(t, c), "cons_gdp_elasticity"])
                                  )
swd['comp_prop'] = swd.cons2 / swd.cons -1
print(swd["comp_prop"].abs().max())
swd.query("year >= 2019")


# Use an index on years only
# Doesn't work because the following has an NA value
## swd.loc[t-1, "price"].pow(swd.loc[t, "cons_price_elasticity"])
# swd.reset_index(inplace=True)
# swd.set_index(["year"], inplace=True)
# # Start one year after the base year so price_{t-1} exists already
# for t in range(gfpmx_data.base_year + 1, gfpmx_data.base_year + 2):#years.max()+1):
#     swd.loc[t, "cons2"] = (swd.loc[t, "cons_constant"]
#                            * swd.loc[t-1, "price"].pow(swd.loc[t, "cons_price_elasticity"])
#                            * swd.loc[t, "gdp"].pow(swd.loc[t, "cons_gdp_elasticity"])
#                            )
# swd.query("year >= 2019")
