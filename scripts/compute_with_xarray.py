#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A script to compute GFPMX equations using xarray

Run this file with:

     ipython -i ~/repos/gftmx/scripts/compute_with_xarray.py

"""

# Third party modules
import numpy
import pandas

# import xarray

# Internal modules
from gftmx.gfpmx_data import gfpmx_data

# Load sawnwood data
swd_all = gfpmx_data.join_sheets("sawn", ["gdp"])

# Separate aggregates from individual countries
selector = swd_all.index.isin(gfpmx_data.country_groups, level="country")
# Copy the slices to new data frames to avoid the warning:
#   "A value is trying to be set on a copy of a slice from a DataFrame.
#   Try using .loc[row_indexer,col_indexer] = value instead"
swd_agg = swd_all[selector].copy()
swd = swd_all[~selector].copy()

# Check that the world aggregate correspond to the sum of constituents
# Compare only columns where the sum makes sense
cols_compare = [
    "cons",
    "cons_usd",
    "exp",
    "exp_usd",
    "imp",
    "imp_usd",
    "prod",
    "prod_usd",
    "gdp",
]
idx = pandas.IndexSlice
world_sum_1 = swd_agg.loc[idx[:, "WORLD"], cols_compare]
world_sum_2 = swd.groupby(["year"]).agg("sum")[cols_compare]
numpy.testing.assert_allclose(world_sum_1, world_sum_2)

# TODO check that the continent aggregates match with the sum of their constituents.

# Number of years and number of countries
years = swd.index.to_frame()["year"].unique()
countries = swd.index.to_frame()["country"].unique()
print("Years:", years)
print("Countries:", countries)
print("Number of lines in the swd data frame:", len(swd))
print(
    "Number of years time the number of countries: ",
    len(years),
    "*",
    len(countries),
    "=",
    len(years) * len(countries),
)
