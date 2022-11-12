#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A script to compute GFPMX demand recursively in a time loop

Run this file with:

     ipython -i ~/repos/gftmx/scripts/compute_sawnwood_equations.py

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
sawn_all = gfpmx_data.join_sheets("sawn", ["gdp"])
indround_all = gfpmx_data.join_sheets("indround")

# TODO place this in gfpmx_data
sawn_all["price_indround_elast"] = sawn_all["price_indround_elast"].astype(
    float, errors="ignore"
)

# Separate aggregates from individual countries
# Select country groups
selector = sawn_all.index.isin(gfpmx_data.country_groups, level="country")
selector = indround_all.index.isin(gfpmx_data.country_groups, level="country")
# Copy the slices to new data frames to avoid the warning:
#   "A value is trying to be set on a copy of a slice from a DataFrame.
#   Try using .loc[row_indexer,col_indexer] = value instead"
sawn_agg = sawn_all[selector].copy()
indround_agg = indround_all[selector].copy()
sawn = sawn_all[~selector].copy()

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
world_sum_1 = sawn_agg.loc[idx[:, "WORLD"], cols_compare]
world_sum_2 = sawn.groupby(["year"]).agg("sum")[cols_compare]
numpy.testing.assert_allclose(world_sum_1, world_sum_2)

# TODO check that the continent aggregates match with the sum of their constituents.

# Number of years and number of countries
years = sawn.index.to_frame()["year"].unique()
countries = sawn.index.to_frame()["country"].unique()
print("Years:", years)
print("Countries:", countries)
print("Number of lines in the sawn data frame:", len(sawn))
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
    """GFPMX domestic production equation 8

    Replace negative values by zero"""
    prod = df["cons"] + df["exp"] - df["imp"]
    prod.loc[prod < 0] = 0
    return prod


# TODO compute the world price of sawnwood based on the industrial roundwood price.
# TODO change the name of df_world, df_primary_world these are not data frames but series
# s_world, s_primary_world)
def compute_world_price(df_world, df_primary_world):
    """GFPMX world price as a function of the roundwood price equation 10"""
    # irw_const = df_agg.xs("WORLD", level="country")["price_constant"]
    # irw_elast = df_agg.xs("WORLD", level="country")["price_indround_elast"]
    # irw_price = df_primary_agg.xs("WORLD", level="country")["price"]
    # const =     elast =
    # irw_price =
    return df_world["price_constant"] * pow(
        df_primary_world["price"], df_world["price_indround_elast"]
    )


def compute_local_price(df, df_agg):
    """GFPMX local price as a function of the world price equation 12"""
    # world_price = df_agg.xs("WORLD", level="country")["price"].iat[0]
    price = df["price_constant"] * pow(
        df_agg.loc[(t, "WORLD"), "price2"], df["price_world_price_elasticity"]
    )
    return price


# Start one year after the base year so price_{t-1} exists already
for t in range(gfpmx_data.base_year + 1, years.max() + 1):
    # Keep `[t]` in square braquets so that years is kept in the index on both sides
    sawn.loc[[t], "price_lag"] = shift_index(sawn.loc[[t - 1], "price"])
    sawn.loc[[t], "tariff_lag"] = shift_index(sawn.loc[[t - 1], "tariff"])
    sawn.loc[[t], "cons2"] = compute_demand(sawn.loc[[t]])
    sawn.loc[[t], "imp2"] = compute_import_demand(sawn.loc[[t]])
    sawn.loc[[t], "exp2"] = compute_export_supply(sawn.loc[[t]])
    sawn.loc[[t], "prod2"] = compute_domestic_production(sawn.loc[[t]])
    sawn_agg.loc[(t, "WORLD"), "price2"] = compute_world_price(
        sawn_agg.loc[(t, "WORLD")], indround_agg.loc[(t, "WORLD")]
    )
    sawn.loc[[t], "price2"] = compute_local_price(sawn.loc[[t]], sawn_agg.loc[[t]])


# Compare only on the country rows
sawn["cons_prop"] = sawn.cons2 / sawn.cons - 1
sawn["imp_prop"] = sawn.imp2 / sawn.imp - 1
sawn["exp_prop"] = sawn.exp2 / sawn.exp - 1
sawn["prod_prop"] = sawn.prod2 / sawn["prod"] - 1
sawn["price_prop"] = sawn.price2 / sawn.price - 1
print(
    "Maximum absolute difference of the proportion between the computed and the original variables."
)
print("Consumption: ", sawn["cons_prop"].abs().max())
print("Import: ", sawn["imp_prop"].abs().max())
print("Export: ", sawn["exp_prop"].abs().max())
print("Production max: ", sawn["prod_prop"].max())
print("Production min: ", sawn["prod_prop"].min())
print("Price: ", sawn["price_prop"].abs().max())
# for col in sawn.columns[sawn.columns.str.contains("_prop$")]:
#     print(sawn[col].describe())


# Post processing quality checks #
# Check that the world imports match the sum of country rows
world_sum_1 = sawn_agg.loc[idx[:, "WORLD"], cols_compare]
world_sum_2 = sawn.groupby(["year"]).agg("sum")[cols_compare]
numpy.testing.assert_allclose(world_sum_1["imp"], world_sum_2["imp"])

# print(sawn.query("year >= 2019")[["price_lag", "tariff_lag", "imp_price_elasticity",
#                                  "imp_gdp_elasticity"]])
# print(sawn.query("year >= 2019")[["price_lag", "gdp", "cons", "cons2"]])
#
# print(sawn.query("year >= 2019")[["exp", "exp2", "exp_prop"]])

# sawn.to_csv("/tmp/sawn.csv") # Open with gx
