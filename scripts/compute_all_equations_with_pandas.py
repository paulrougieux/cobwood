#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" This script is deprecated, see the xarray version.

Functions to implement equations in the paper

    Buongiorno, J. (2021). GFPMX: A Cobweb Model of the Global Forest Sector, with
    an Application to the Impact of the COVID-19 Pandemic. Sustainability, 13(10),
    5507.

    https://www.mdpi.com/2071-1050/13/10/5507

    Local link

    ~/repos//bioeconomy_papers/literature/buongiorno2021_gfpmx_a_cobweb_model_of_the_global_forest_sector_with_an_application_to_the_impact_of_the_covid_19_pandemic.pdf

Excel file "~/large_models/GFPMX-8-6-2021.xlsx"

A script to compute GFPMX equations recursively in a time loop

TODO: rename this script to compute_all_equations_with_pandas.py

Run this file with:

     ipython -i ~/repos/cobwood/scripts/compute_all_equations.py

Equation numbers in this script refer to the paper:

    Buongiorno, J. (2021). GFPMX: A Cobweb Model of the Global Forest Sector, with
    an Application to the Impact of the COVID-19 Pandemic. Sustainability, 13(10),
    5507.

    https://www.mdpi.com/2071-1050/13/10/5507

    Local link

    ~/repos//bioeconomy_papers/literature/buongiorno2021_gfpmx_a_cobweb_model_of_the_global_forest_sector_with_an_application_to_the_impact_of_the_covid_19_pandemic.pdf

Excel file "~/large_models/GFPMX-8-6-2021.xlsx"
"""
import numpy

from cobwood.gfpmx_data import GFPMXData

# These functions have been moved back out of the package, into this script
# from cobwood.gfpmx_functions_pandas import (
#     shift_index,
#     compute_demand,
#     compute_import_demand,
#     compute_export_supply,
#     compute_domestic_production,
#     compute_world_price,
#     compute_local_price,
# )
from cobwood.gfpmx_qaqc import (
    check_world_aggregates,
    check_nrows_years_countries,
    compare_to_original_cobwood,
)

# Load data
gfpmx_data = GFPMXData(data_dir="gfpmx_8_6_2021")
indround_agg = gfpmx_data.get_agg_rows("indround")
pulp_agg = gfpmx_data.get_agg_rows("pulp")
pulp = gfpmx_data.get_country_rows("pulp", ["gdp"])
sawn = gfpmx_data.get_country_rows("sawn", ["gdp"])
sawn_agg = gfpmx_data.get_agg_rows("sawn", ["gdp"])
fuel = gfpmx_data.get_country_rows("fuel", ["gdp"])
fuel_agg = gfpmx_data.get_agg_rows("fuel", ["gdp"])
# TODO: remove rows containing "World prod/cons" or simply that don't have a FAOSTAT name from
# the input data pre-processed in "~/rp/cobwood/scripts/gfpmx_spreadsheet_to_csv.py"
panel = gfpmx_data.get_country_rows("panel", ["gdp"])
panel_agg = gfpmx_data.get_agg_rows("panel", ["gdp"])
paper = gfpmx_data.get_country_rows("paper", ["gdp"])
paper_agg = gfpmx_data.get_agg_rows("paper", ["gdp"])

# Check that world aggregates correspond to the sum of countries
check_world_aggregates(fuel, fuel_agg)
check_world_aggregates(sawn, sawn_agg)
check_world_aggregates(panel, panel_agg, rtol=1e-4)
check_world_aggregates(paper, paper_agg)

# Display the number of countries and years
print(check_nrows_years_countries(fuel, "fuel"))
print(check_nrows_years_countries(sawn, "sawn"))
print(check_nrows_years_countries(panel, "panel"))
print(check_nrows_years_countries(paper, "paper"))


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


def compute_world_price(s_world, s_primary_world):
    """GFPMX world price as a function of the input price
    - World price of f, s, u, l as a function of the roundwood price equation 10
    - World price of paper as a function of the pulp price equation 11
    """
    return s_world["price_constant"] * pow(
        s_primary_world["price"], s_world["price_input_elast"]
    )


def compute_local_price(df, s_world):
    """GFPMX local price as a function of the world price equation 12"""
    # world_price = s_world.xs("WORLD", level="country")["price"].iat[0]
    price = df["price_constant"] * pow(
        s_world.loc["price2"], df["price_world_price_elasticity"]
    )
    return price


def compute_end_product_time_step(t, df, df_agg, df_prim_agg):
    """Compute a time step for the given product

    Attention! This will edit the input data frame by reference.
    It will edit the following new columns:

        ['price_lag', 'tariff_lag', 'cons2', 'imp2',
        'exp2', 'prod2', 'price2']

    :param df data frame: end product data at time step t
    :param df_agg data frame: end product data aggregated
    :param df data frame: end product data at time step t
    :return computed variables at time step t

    Usage:

        >>> compute_end_product_time_step(2019, sawn, sawn_agg, indround_agg)
    """
    # Keep `[t]` in square braquets so that years is kept in the index on both sides
    df.loc[[t], "price_lag"] = shift_index(df.loc[[t - 1], "price"])
    df.loc[[t], "tariff_lag"] = shift_index(df.loc[[t - 1], "tariff"])
    df.loc[[t], "cons2"] = compute_demand(df.loc[[t]])
    df.loc[[t], "imp2"] = compute_import_demand(df.loc[[t]])
    df.loc[[t], "exp2"] = compute_export_supply(df.loc[[t]])
    df.loc[[t], "prod2"] = compute_domestic_production(df.loc[[t]])
    df_agg.loc[(t, "WORLD"), "price2"] = compute_world_price(
        df_agg.loc[(t, "WORLD")], df_prim_agg.loc[(t, "WORLD")]
    )
    df.loc[[t], "price2"] = compute_local_price(df.loc[[t]], df_agg.loc[(t, "WORLD")])


years = sawn.index.to_frame()["year"].unique()
# Start one year after the base year so price_{t-1} exists already
for t in range(gfpmx_data.base_year + 1, years.max() + 1):
    # The world price of secondary products are based in the price of industrial roundwood
    compute_end_product_time_step(t, fuel, fuel_agg, indround_agg)
    compute_end_product_time_step(t, sawn, sawn_agg, indround_agg)
    compute_end_product_time_step(t, panel, panel_agg, indround_agg)
    # The world price of paper and paper board is based on the price of wood pulp
    compute_end_product_time_step(t, paper, paper_agg, pulp_agg)
    # Compute domestic demand for wood pulp


compare_to_original_cobwood(fuel)
compare_to_original_cobwood(sawn)
compare_to_original_cobwood(panel)
compare_to_original_cobwood(paper)
