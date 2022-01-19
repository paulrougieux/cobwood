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
# Load sawnwood elasticities
gfpmx_data.get_sheet_wide("sawncons")

# Number of years and number of countries
n_years = len(swd.year.unique())
n_countries = len(swd.country.unique())
print("Years:", n_years)
print("Countries:", n_countries)
print("Lines in the swd data frame:", len(swd), ".",
      n_years, "*", n_countries, "=", n_years * n_countries)


# swd_cons.drop(columns = [ 'faostat_name', 'price'], inplace=True)
# 
# # Compute the consumption equation
# swd_cons['value2'] = swd_cons.constant * swd_cons['price_lag'].pow(swd_cons.price_elasticity) * \
#     swd_cons.gdp.pow(swd_cons.gdp_elasticity)
# 
# swd_cons['comp_prop'] = swd_cons.value2 / swd_cons.value -1
# # Don't display rows with NA values
# swd_cons.query("price_lag==price_lag & gdp_elasticity==gdp_elasticity")
