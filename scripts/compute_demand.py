#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A script to compute GFPMX demand recursively in a time loop

Run this file with:

     ipython -i ~/rp/gftmx/scripts/compute_demand.py

"""

from gftmx.gfpmx_data import gfpmx_data
# Load sawnwood data
swd = gfpmx_data.join_sheets('sawn')
swd.head()

# Number of years and number of countries
n_years = swd.index.to_frame().year.unique()
n_countries = swd.index.to_frame().country.unique()
print("Years:", n_years)
print("Countries:", n_countries)
print("Number of lines in the swd data frame:", len(swd))
print("Number of years time the number of countries: ",
      len(n_years), "*", len(n_countries), "=", len(n_years) * len(n_countries))


# Compute the consumption equation
# TODO add a loop based on index for the recursive computation of price_{t_1}
swd["cons2"] = swd["cons_constant"] * swd['cons_price_lag'].pow(swd.cons_price_elasticity) * \
    swd.cons_gdp.pow(swd.cons_gdp_elasticity)

swd['comp_prop'] = swd_cons.cons2 / swd_cons.cons -1
# # Don't display rows with NA values
# swd_cons.query("price_lag==price_lag & gdp_elasticity==gdp_elasticity")
