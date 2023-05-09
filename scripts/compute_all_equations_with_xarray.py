"""This scripts computes all GFPMx equations using xarray

Usage:

    ipython -i ~/repos/gftmx/scripts/compute_all_equations_with_xarray.py

See also:

- A drawing illustrating the model structure in
  draft_articles/gftm_degrowth/model_structure.odg

- Buongiorno, J. (2021). GFPMX: A Cobweb Model of the Global Forest Sector,
  with an Application to the Impact of the COVID-19 Pandemic. Sustainability,
  13(10), 5507. https://www.mdpi.com/2071-1050/13/10/5507

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

import warnings
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
panel_ref = gfpmx_data.convert_sheets_to_dataset("panel")
pulp_ref = gfpmx_data.convert_sheets_to_dataset("pulp")
paper_ref = gfpmx_data.convert_sheets_to_dataset("paper")
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


other = remove_after_base_year_and_copy(other_ref, 2018)
fuel = remove_after_base_year_and_copy(fuel_ref, 2018)
indround = remove_after_base_year_and_copy(indround_ref, 2018)
# Use an underscore so that we don't overwrite the python round() function
round_ = remove_after_base_year_and_copy(round_ref, 2018)
sawn = remove_after_base_year_and_copy(sawn_ref, 2018)
panel = remove_after_base_year_and_copy(panel_ref, 2018)
pulp = remove_after_base_year_and_copy(pulp_ref, 2018)
paper = remove_after_base_year_and_copy(paper_ref, 2018)

# Add GDP projections to the datasets
sawn["gdp"] = gdp
round_["gdp"] = gdp
panel["gdp"] = gdp
fuel["gdp"] = gdp
paper["gdp"] = gdp


def consumption(ds: xarray.Dataset, t: int) -> xarray.DataArray:
    """Compute consumption equation 1"""
    return (
        ds["cons_constant"]
        * pow(ds["price"].loc[COUNTRIES, t - 1], ds["cons_price_elasticity"])
        * pow(ds["gdp"].loc[COUNTRIES, t], ds["cons_gdp_elasticity"])
    )


def consumption_pulp(
    ds: xarray.Dataset, ds_paper: xarray.Dataset, t: int
) -> xarray.DataArray:
    """Compute the Domestic Demand for Wood Pulp equation 2"""
    return (
        ds["cons_constant"]
        * pow(ds["price"].loc[COUNTRIES, t - 1], ds["cons_price_elasticity"])
        * pow(
            ds_paper["prod"].loc[COUNTRIES, t], ds["cons_paper_production_elasticity"]
        )
    )


def import_demand_pulp(
    ds: xarray.Dataset, ds_paper: xarray.Dataset, t: int
) -> xarray.DataArray:
    return


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


def import_demand_indround():
    """Compute the import demand of industrial roundwood"""


def compute_end_product_time_step(
    ds: xarray.Dataset, ds_primary: xarray.Dataset, t: int
) -> None:
    """Compute consumption, production trade and price equations corresponding
    to a semi finished products (end product for the purpose of this model).

    ! This function modifies the input data set `ds` for the given time step.
    """
    ds["cons"].loc[COUNTRIES, t] = consumption(ds, t)
    ds["imp"].loc[COUNTRIES, t] = import_demand(ds, t)
    ds["exp"].loc[COUNTRIES, t] = export_supply(ds, t)
    ds["prod"].loc[COUNTRIES, t] = production(ds, t)
    ds["price"].loc["WORLD", t] = world_price(ds, ds_primary, t)
    ds["price"].loc[COUNTRIES, t] = local_price(ds, t)


#########################
# Compute one time step #
#########################
year = 2019

# 1. Compute stock growth and drain from stock and production at t-1
other["stock"].loc[COUNTRIES, year] = forest_stock(other, round_, year)

# 2. Compute cons, trade, prod and prices of secondary products
compute_end_product_time_step(sawn, indround, year)
compute_end_product_time_step(fuel, indround, year)
compute_end_product_time_step(panel, indround, year)
compute_end_product_time_step(paper, pulp, year)

# 3. Compute cons, prod and trade of primary products
# TODO: implement "Import Demand for Wood Pulp" equation 5
# TODO: compute the import demand for industrial roundwood
# TODO: compute the export supply of industrial roundwood
# indroundexp =MAX(0,$F2*$IndroundImp.CI$182+$G2)
# sawnexp =MAX(0,$F2*$SawnImp.CI$182+$G2)

pulp["cons"].loc[COUNTRIES, year] = consumption_pulp(pulp, paper, year)

indround["exp"].loc[COUNTRIES, year] = export_supply(indround, year)

# TODO: Compute the consumption of industrial roundwood equation 3
consumption_indround

# TODO: Compute production and trade of industrial roundwood
indround["price"].loc["WORLD", year] = world_price_indround(indround, other, year)

##########
# Checks #
##########
# Comparison between sawn modified in place by the
# compute_end_product_time_step() function
# and sawn2 computed below
sawn2 = sawn.copy(deep=True)
sawn2["cons"].loc[COUNTRIES, year] = consumption(sawn2, year)
sawn2["imp"].loc[COUNTRIES, year] = import_demand(sawn2, year)
sawn2["exp"].loc[COUNTRIES, year] = export_supply(sawn2, year)
sawn2["prod"].loc[COUNTRIES, year] = production(sawn2, year)
warnings.warn("Compute world price of indround (then delete this warning)")
# TODO the world price of indround is required here
sawn2["price"].loc["WORLD", year] = world_price(sawn2, indround, year)
sawn2["price"].loc[COUNTRIES, year] = local_price(sawn2, year)
assert sawn.equals(sawn2)


# Compute roundwood as the sum of industrial round wood and fuel wood
round_["prod"].loc[COUNTRIES, year] = (
    indround["prod"].loc[COUNTRIES, year] + fuel["prod"].loc[COUNTRIES, year]
)


def compare_to_ref(
    ds: xarray.Dataset, ds_ref: xarray.Dataset, vars_to_compare: list, t: int
):
    """Compare the computed dataset to the reference dataset for the given t"""
    print(f"Checking {ds.product} {vars_to_compare}")
    for var in vars_to_compare:
        rtol = 1e-7
        if var == "prod":
            rtol = 1e-2
        try:
            assert_allclose(
                ds[var].loc[COUNTRIES, t],
                ds_ref[var].loc[COUNTRIES, t],
                rtol=rtol,
            )
        except AssertionError as e:
            print(f"{ds.product}, {var}")
            raise e
    print("    OK")


ciep_vars = ["cons", "imp", "exp", "prod"]
compare_to_ref(sawn, sawn_ref, ciep_vars, 2019)
compare_to_ref(panel, panel_ref, ciep_vars, 2019)
compare_to_ref(paper, paper_ref, ciep_vars, 2019)
compare_to_ref(pulp, pulp_ref, ["cons"], 2019)


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
