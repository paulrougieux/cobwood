#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A script to compute GFPMX equations recursively in a time loop

Run this file with:

     ipython -i ~/repos/gftmx/scripts/compute_all_equations.py

Equation numbers in this script refer to the paper:

    Buongiorno, J. (2021). GFPMX: A Cobweb Model of the Global Forest Sector, with
    an Application to the Impact of the COVID-19 Pandemic. Sustainability, 13(10),
    5507.

    https://www.mdpi.com/2071-1050/13/10/5507

    Local link

    ~/repos//bioeconomy_papers/literature/buongiorno2021_gfpmx_a_cobweb_model_of_the_global_forest_sector_with_an_application_to_the_impact_of_the_covid_19_pandemic.pdf

Excel file "~/large_models/GFPMX-8-6-2021.xlsx"
"""

from gftmx.gfpmx_data import gfpmx_data
from gftmx.gfpmx_functions import (
    shift_index,
    compute_demand,
    compute_import_demand,
    compute_export_supply,
    compute_domestic_production,
    compute_world_price,
    compute_local_price,
)
from gftmx.gfpmx_qaqc import (
    check_world_aggregates,
    check_nrows_years_countries,
    compare_to_original_gftmx,
)

# Load data
sawn = gfpmx_data.get_country_rows("sawn", ["gdp"])
sawn_agg = gfpmx_data.get_agg_rows("sawn", ["gdp"])
fuel = gfpmx_data.get_country_rows("fuel", ["gdp"])
fuel_agg = gfpmx_data.get_agg_rows("fuel", ["gdp"])
indround_agg = gfpmx_data.get_agg_rows("indround")

# Check that world aggregates correspond to the sum of countries
check_world_aggregates(sawn, sawn_agg)
check_world_aggregates(fuel, fuel_agg)
print(check_nrows_years_countries(sawn, "sawn"))
print(check_nrows_years_countries(fuel, "fuel"))


def compute_end_product_time_step(t, df, df_agg, df_prim_agg):
    """Compute a time step for the given product

    Attention! This will edit the input data frame by reference.

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
    compute_end_product_time_step(t, sawn, sawn_agg, indround_agg)
    compute_end_product_time_step(t, fuel, fuel_agg, indround_agg)

compare_to_original_gftmx(sawn)
compare_to_original_gftmx(fuel)
