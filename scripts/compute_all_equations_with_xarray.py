"""This scripts computes all GFPMx equations using xarray

Usage:

    ipython -i ~/repos/gftmx/scripts/compute_all_equations_with_xarray.py

Advantages of using xarray over pandas:

- The shift_index() function is not needed any more, we can call
  sawn["price"].loc[:, t - 1] directly.


TODO:

- Evaluate whether it is better to keep countries and aggregates in the same dataset.

  Option A If countries and aggregates are in the same dataset, consumption should be
  computed for countries only first, the aggregates computed later.

        ds["cons_constant"]
        * pow(ds["price"].loc[COUNTRIES, t - 1], ds["cons_price_elasticity"])
        * pow(ds["gdp"].loc[COUNTRIES, t], ds["cons_gdp_elasticity"])

  World price is

        ds["price_constant"].loc["WORLD"]
        * pow(ds_primary["price"].loc["WORLD", t], ds["price_input_elast"].loc["WORLD"])

  Should the .loc["WORLD"] and .loc[COUNTRIES] be done when the function is
  called? No better to leave no ambiguity.


  Option B If there was a dataset of countries only and a dataset of aggregates only we
  would compute consumption as such:

        ds["cons_constant"]
        * pow(ds["price"].loc[:, t - 1], ds["cons_price_elasticity"])
        * pow(ds["gdp"].loc[:, t], ds["cons_gdp_elasticity"])

  World prices would be computed as:

        ds_agg["price_constant"].loc["WORLD"]
        * pow(ds_primary_agg["price"].loc["WORLD", t], ds_agg["price_input_elast"].loc["WORLD"])

"""

import numpy as np
from numpy.testing import assert_allclose
import xarray

# import pandas
# import seaborn

from gftmx.gfpmx_data import gfpmx_data
from gftmx.gfpmx_data import convert_to_2d_array

# Load reference data
other_ref = gfpmx_data.convert_sheets_to_dataset("other")
indround_ref = gfpmx_data.convert_sheets_to_dataset("indround")
round_ref = gfpmx_data.convert_sheets_to_dataset("round")
fuel_ref = gfpmx_data.convert_sheets_to_dataset("fuel")
sawn_ref = gfpmx_data.convert_sheets_to_dataset("sawn")
pulp_ref = gfpmx_data.convert_sheets_to_dataset("pulp")
panel_ref = gfpmx_data.convert_sheets_to_dataset("panel")
gdp = convert_to_2d_array(gfpmx_data.get_sheet_wide("gdp"))

COUNTRY_AGGREGATES = [
    "WORLD",
    "AFRICA",
    "NORTH AMERICA",
    "SOUTH AMERICA",
    "ASIA",
    "OCEANIA",
    "EUROPE",
]
COUNTRIES = sawn_ref.country[~sawn_ref.country.isin(COUNTRY_AGGREGATES)]

######################################################
# Erase data after base year and copy the data frame #
######################################################
# Using a mask makes the dataset return an error on loc selection
# base_year = 2018
# mask = sawn.coords["year"] > base_year
# sawn = xarray.where(mask, np.nan, sawn_ref).copy()
# sawn["price"].loc[:,t-1]
# # returns KeyError: 2018
# # But selecting the original data works fine
# sawn_ref["price"].loc[:,t-1]
# --> Make a reproducible example and ask on Stackoverflow why this is the case.
# We will compute demand from the base_year + 1


def remove_after_base_year_and_copy(ds: xarray.Dataset, base_year):
    """Remove values after the base year and return a deep copy of the
    input dataset, i.e. the input dataset is not modified.
    """
    ds_out = ds.copy(deep=True)
    for x in ds_out.data_vars:
        if len(ds_out[x].dims) == 2:
            ds_out[x].loc[dict(year=ds_out.coords["year"] > base_year)] = np.nan
    return ds_out


fuel = remove_after_base_year_and_copy(fuel_ref, 2018)
indround = remove_after_base_year_and_copy(indround_ref, 2018)
other = remove_after_base_year_and_copy(other_ref, 2018)
panel = remove_after_base_year_and_copy(panel_ref, 2018)
pulp = remove_after_base_year_and_copy(pulp_ref, 2018)
# Use an underscore so that we don't overwrite the python round() function
round_ = remove_after_base_year_and_copy(round_ref, 2018)
sawn = remove_after_base_year_and_copy(sawn_ref, 2018)


def consumption(ds: xarray.Dataset, t: int) -> xarray.DataArray:
    """Compute consumption equation 1"""
    return (
        ds["cons_constant"]
        * pow(ds["price"].loc[COUNTRIES, t - 1], ds["cons_price_elasticity"])
        * pow(ds["gdp"].loc[COUNTRIES, t], ds["cons_gdp_elasticity"])
    )


def import_demand(ds: xarray.Dataset, t: int) -> xarray.DataArray:
    """Compute import demand equation 4"""
    return (
        ds["imp_constant"]
        * pow(
            ds["price"].loc[COUNTRIES, t - 1] * (1 + ds["tariff"].loc[:, t - 1]),
            ds["imp_price_elasticity"],
        )
        * pow(ds["gdp"].loc[COUNTRIES, t], ds["imp_gdp_elasticity"])
    )


def export_supply(ds: xarray.Dataset, t: int) -> xarray.DataArray:
    """Compute export supply equation 7

    Replace negative values by zero."""
    world_imp = ds["imp"].loc[COUNTRIES, t].sum()
    exp = (
        ds["exp_marginal_propensity_to_export"].loc[COUNTRIES] * world_imp
        + ds["exp_constant"]
    )
    return np.maximum(exp, 0)


def production(ds: xarray.Dataset, t: int) -> xarray.DataArray:
    """Compute domestic production equation 8
    Replace negative values by zero
    """
    prod = (
        ds["cons"].loc[COUNTRIES, t]
        + ds["exp"].loc[COUNTRIES, t]
        - ds["imp"].loc[COUNTRIES, t]
    )
    return np.maximum(prod, 0)


def world_price_indround(
    ds_indround: xarray.Dataset, ds_other: xarray.Dataset, t: int
) -> xarray.DataArray:
    """Compute the world price of industrial roundwood equation 9"""
    return (
        ds_indround["price_constant"].loc["WORLD"]
        * pow(
            ds_indround["prod"].loc["WORLD", t],
            ds_indround["price_world_price_elasticity"].loc["WORLD"],
        )
        * pow(
            ds_other["stock"].loc["WORLD", t],
            ds_indround["price_stock_elast"].loc["WORLD"],
        )
    )


def world_price(
    ds: xarray.Dataset, ds_primary: xarray.Dataset, t: int
) -> xarray.DataArray:
    """Compute the world price equation 10
    as a function of the input price
    """
    return ds["price_constant"].loc["WORLD"] * pow(
        ds_primary["price"].loc["WORLD", t], ds["price_input_elast"].loc["WORLD"]
    )


def local_price(ds: xarray.Dataset, t: int) -> xarray.DataArray:
    """Compute the local price equation 12"""
    return ds["price_constant"].loc[COUNTRIES] * pow(
        ds["price"].loc["WORLD", t], ds["price_world_price_elasticity"].loc[COUNTRIES]
    )


def forest_stock(
    ds: xarray.Dataset, ds_round: xarray.Dataset, t: int
) -> xarray.DataArray:
    """Compute the forest stock expressed as growth drain equation 15

    Notes:
    - Roundwood is the sum of industrial round wood and fuel wood.
    - Replaces negative values by zero
    - Converts the stock from thousand m3 to million m3
        - TODO remove this conversion? Currently kept for comparison purposes with GFPMx.
            - Other units are in 1000 m3, should the whole model be harmonized to m3?
    """
    stock = (
        ds["stock"].loc[COUNTRIES, t - 1]
        * (1 + ds["stock_stock_growth_rate_without_harvest"].loc[COUNTRIES])
        - ds["stock_harvest_effect_on_stock"].loc[COUNTRIES]
        * ds_round["prod"].loc[COUNTRIES, t - 1]
        / 1000
    )
    return np.maximum(stock, 0)


def consumption_indround(
    ds_indround: xarray.Dataset,
    ds_sawn: xarray.Dataset,
    ds_panel: xarray.Dataset,
    ds_pulp: xarray.Dataset,
    t: int,
) -> xarray.DataArray:
    """Domestic demand for industrial roundwood equation 3"""
    # TODO: compute the domestic demand for industrial roundwood
    cons = pow(
        ds_indround["price"].loc[COUNTRIES, t - 1],
        ds_indround["cons_price_elasticity"].loc[COUNTRIES],
    ) * pow(
        ds_sawn["prod"].loc[COUNTRIES, t]
        + ds_panel["prod"].loc[COUNTRIES, t]
        + ds_pulp["prod"].loc[COUNTRIES, t],
        ds_indround["cons_products_elasticity"],
    )
    return np.maximum(cons, 0)


def import_demand_indround():
    """Compute the import demand of industrial roundwood"""


def compute_end_product_time_step(
    ds: xarray.Dataset, ds_primary: xarray.Dataset, t: int
) -> None:
    """Compute the

    ! This function modifies the input data set `ds` for the given time step.
    """
    ds["cons"].loc[COUNTRIES, t] = consumption(ds, t)
    ds["imp"].loc[COUNTRIES, t] = import_demand(ds, t)
    ds["exp"].loc[COUNTRIES, t] = export_supply(ds, t)
    ds["prod"].loc[COUNTRIES, t] = production(ds, t)
    ds["price"].loc["WORLD", t] = world_price(ds, ds_primary, t)
    ds["price"].loc[COUNTRIES, t] = local_price(ds, t)


# Add GDP projections to the datasets
sawn["gdp"] = gdp
round_["gdp"] = gdp

# Compute one time step
year = 2019

# 1. Compute stock growth and drain from stock and production at t-1
other["stock"].loc[COUNTRIES, year] = forest_stock(other, round_, year)
# 2. Compute cons, prod, trade and prices of secondary products
# Consumption is driven by GDP and demand at t-1

# Compare
sawn2 = sawn.copy(deep=True)
compute_end_product_time_step(year, sawn2, indround)

sawn["cons"].loc[COUNTRIES, year] = consumption(sawn, year)
sawn["imp"].loc[COUNTRIES, year] = import_demand(sawn, year)
sawn["exp"].loc[COUNTRIES, year] = export_supply(sawn, year)
sawn["prod"].loc[COUNTRIES, year] = production(sawn, year)
sawn["price"].loc["WORLD", year] = world_price(sawn, indround, year)
sawn["price"].loc[COUNTRIES, year] = local_price(sawn, year)
assert sawn.equals(sawn2)

# 3. Compute cons, prod and trade of primary products
# TODO: compute the import demand for industrial roundwood
# TODO: compute the export supply of industrial roundwood
indround["exp"].loc[COUNTRIES, year] = export_supply(indround, year)
# TODO: compute production and trade of industrial roundwood
indround["price"].loc["WORLD", year] = world_price_indround(indround, other, year)

# Compute roundwood as the sum of industrial round wood and fuel wood
round_["prod"].loc[COUNTRIES, year] = (
    indround["prod"].loc[COUNTRIES, year] + fuel["prod"].loc[COUNTRIES, year]
)

# Compare computed results to the reference dataset
vars_to_compare = ["cons", "imp", "exp", "prod"]
year = 2019
for var in vars_to_compare:
    print(f"Checking {var}")
    rtol = 1e-7
    if var == "prod":
        rtol = 1e-2
    assert_allclose(
        sawn[var].loc[COUNTRIES, year],
        sawn_ref[var].loc[COUNTRIES, year],
        rtol=rtol,
    )
# Compare world price
assert_allclose(sawn["price"].loc["WORLD", year], sawn_ref["price"].loc["WORLD", year])

# Comparison in case of mismatch
sawn_df = sawn.loc[dict(country=COUNTRIES, year=year)].to_pandas().reset_index()
sawn_ref_df = sawn_ref.loc[dict(country=COUNTRIES, year=year)].to_pandas().reset_index()
cols_to_check = ["cons", "imp", "exp", "prod"]
print(sawn_df[cols_to_check])
print(sawn_ref_df[cols_to_check])
sawn_df["prod_diff"] = sawn_df["prod"] / sawn_ref_df["prod"] - 1
sawn_df["cons_diff"] = sawn_df["cons"] / sawn_ref_df["cons"] - 1
print(sawn_df[["cons_diff", "prod_diff"]].describe())
sawn_df[["country"] + cols_to_check + ["prod_diff"]].sort_values(
    "prod_diff", ascending=False
)
print(sawn_ref_df[["country"] + cols_to_check])


# Plot comparison
# sawn_df["reference"] = "no"
# sawn_ref_df["reference"] = "yes"
# sawn_comp = pandas.concat([sawn_df, sawn_ref_df])
# p = seaborn.scatterplot(x="country", y="prod", hue="reference", data=sawn_comp)
# plt.xticks(rotation=90)
# plt.show()
