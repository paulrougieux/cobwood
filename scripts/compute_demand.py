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

"""

# Third party modules
import numpy

# Internal modules
from gftmx.gfpmx_data import gfpmx_data

# Load sawnwood data
swd_all = gfpmx_data.join_sheets("sawn", ["gdp"])

# Remove aggregates
country_aggregates = [
    "WORLD",
    "AFRICA",
    "NORTH AMERICA",
    "SOUTH AMERICA",
    "ASIA",
    "OCEANIA",
    "EUROPE",
]
swd_agg = swd_all.loc[(slice(None), country_aggregates), :]
swd = swd_all.query("country not in @country_aggregates")
swd.head()

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

# swd.to_csv("/tmp/swd.csv") # Open with gx


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
    """GFPMX export supply equation 8"""
    # TODO remove world and continent aggregates from swd place them in a separate table,
    # check that the aggregates match with the sum of their constituents.
    # TODO Use the sum of all countries directly here
    t = df.index.to_frame()["year"].unique()[0]
    world_imp = df.loc[(t, "WORLD"), "imp"]
    exp = df["exp_marginal_propensity_to_export"] * world_imp + df["exp_constant"]
    # Use numpy.maximum to propagate NA values
    return numpy.maximum(exp, 0)


# Start one year after the base year so price_{t-1} exists already
for t in range(gfpmx_data.base_year + 1, years.max() + 1):
    swd.loc[[t], "price_lag"] = shift_index(swd.loc[[t - 1], "price"])
    swd.loc[[t], "tariff_lag"] = shift_index(swd.loc[[t - 1], "tariff"])
    swd.loc[[t], "cons2"] = compute_demand(swd.loc[[t]])
    swd.loc[[t], "imp2"] = compute_import_demand(swd.loc[[t]])
    swd.loc[[t], "exp2"] = compute_export_supply(swd.loc[[t]])

# Compare only on the world countries
# World and continents aggregates have NA values at this stage
swd["cons_prop"] = swd.cons2 / swd.cons - 1
swd["imp_prop"] = swd.imp2 / swd.imp - 1
swd["exp_prop"] = swd.exp2 / swd.exp - 1
print("Consumption: ", swd["cons_prop"].abs().max())
print("Import: ", swd["imp_prop"].abs().max())
print("Export: ", swd["exp_prop"].abs().max())

# print(swd.query("year >= 2019")[["price_lag", "tariff_lag", "imp_price_elasticity",
#                                  "imp_gdp_elasticity"]])
# print(swd.query("year >= 2019")[["price_lag", "gdp", "cons", "cons2"]])
#
# print(swd.query("year >= 2019")[["exp", "exp2", "exp_prop"]])
