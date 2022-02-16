#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A script to compute GFPMX demand recursively in a time loop

Run this file with:

     ipython -i ~/repos/gftmx/scripts/compute_demand.py

Equation numbers in this script refer to the paper:

    Buongiorno, J. (2021). GFPMX: A Cobweb Model of the Global Forest Sector, with
    an Application to the Impact of the COVID-19 Pandemic. Sustainability, 13(10),
    5507.

    https://www.mdpi.com/2071-1050/13/10/5507

    Local link

    ~/repos//bioeconomy_papers/literature/buongiorno2021_gfpmx_a_cobweb_model_of_the_global_forest_sector_with_an_application_to_the_impact_of_the_covid_19_pandemic.pdf

Excel file "~/large_models/GFPMX-8-6-2021.xlsx"
"""

# Third party modules
import numpy
import pandas

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


def shift_index(x):
    """Update the index of a lagged variable
    To store last year's prices in a "price_lag" column at year t.
    We first need to update the index from year t-1 to year t.
    Otherwise assignation of .loc[[t], "price_lag"] would contain NA values.

    :param x pandas series input variable indexed by year and country
    :return pandas series
    """
    df = x.reset_index()
    df["year"] = df["year"] + 1
    x_lag = df.set_index(x.index.names)[x.name]
    return x_lag


def compute_demand(df):
    """GFPMX demand equation 1"""
    return (
        df["cons_constant"]
        * df["price_lag"].pow(df["cons_price_elasticity"])
        * df["gdp"].pow(df["cons_gdp_elasticity"])
    )


def compute_import_demand(df):
    """GFPMX import demand equation 4"""
    return (
        df["imp_constant"]
        * (df["price_lag"] * (1 + df["tariff_lag"])).pow(df["imp_price_elasticity"])
        * df["gdp"].pow(df["imp_gdp_elasticity"])
    )


def compute_export_supply(df):
    """GFPMX export supply equation 7"""
    world_imp = df["imp"].sum()
    exp = df["exp_marginal_propensity_to_export"] * world_imp + df["exp_constant"]
    # Use numpy.maximum to propagate NA values
    return numpy.maximum(exp, 0)


def compute_domestic_production(df):
    """GFPMX domestic production equation 8"""
    # TODO: replace minus values by zero
    prod = df["cons"] + df["exp"] - df["imp"]
    # prod.loc[prod <0 ] = 0
    return prod


# Start one year after the base year so price_{t-1} exists already
for t in range(gfpmx_data.base_year + 1, years.max() + 1):
    swd.loc[[t], "price_lag"] = shift_index(swd.loc[[t - 1], "price"])
    swd.loc[[t], "tariff_lag"] = shift_index(swd.loc[[t - 1], "tariff"])
    swd.loc[[t], "cons2"] = compute_demand(swd.loc[[t]])
    swd.loc[[t], "imp2"] = compute_import_demand(swd.loc[[t]])
    swd.loc[[t], "exp2"] = compute_export_supply(swd.loc[[t]])
    swd.loc[[t], "prod2"] = compute_domestic_production(swd.loc[[t]])

# Compare only on the country rows
swd["cons_prop"] = swd.cons2 / swd.cons - 1
swd["imp_prop"] = swd.imp2 / swd.imp - 1
swd["exp_prop"] = swd.exp2 / swd.exp - 1
swd["prod_prop"] = swd.prod2 / swd["prod"] - 1
print("Consumption: ", swd["cons_prop"].abs().max())
print("Import: ", swd["imp_prop"].abs().max())
print("Export: ", swd["exp_prop"].abs().max())
print("Production: ", swd["prod_prop"].abs().max())

# Post processing quality checks #
# Check that the world imports match the sum of country rows
world_sum_1 = swd_agg.loc[idx[:, "WORLD"], cols_compare]
world_sum_2 = swd.groupby(["year"]).agg("sum")[cols_compare]
numpy.testing.assert_allclose(world_sum_1["imp"], world_sum_2["imp"])

# print(swd.query("year >= 2019")[["price_lag", "tariff_lag", "imp_price_elasticity",
#                                  "imp_gdp_elasticity"]])
# print(swd.query("year >= 2019")[["price_lag", "gdp", "cons", "cons2"]])
#
# print(swd.query("year >= 2019")[["exp", "exp2", "exp_prop"]])

# swd.to_csv("/tmp/swd.csv") # Open with gx
