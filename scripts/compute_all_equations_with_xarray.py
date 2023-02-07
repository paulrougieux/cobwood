"""This scripts computes all GFPMx equations using xarray

Usage:

    ipython -i ~/repos/gftmx/scripts/compute_all_equations_with_xarray.py

Advantages of using xarray over pandas:

- The shift_index() function is not needed any more, we can call
  sawn["price"].loc[:, t - 1] directly.

"""

import numpy as np
from numpy.testing import assert_allclose

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


def remove_after_base_year_and_copy(ds, base_year):
    """Remove values after the base year and return a deep copy of the
    input dataset, i.e. the input dataset is not modified.
    """
    ds_out = ds.copy(deep=True)
    for x in ds_out.data_vars:
        if len(ds_out[x].dims) == 2:
            ds_out[x].loc[dict(year=ds_out.coords["year"] > base_year)] = np.nan
    return ds_out


# Use and underscore so that we don't overwrite the python round() function
round_ = remove_after_base_year_and_copy(round_ref, 2018)
indround = remove_after_base_year_and_copy(indround_ref, 2018)
fuel = remove_after_base_year_and_copy(fuel_ref, 2018)
sawn = remove_after_base_year_and_copy(sawn_ref, 2018)
other = remove_after_base_year_and_copy(other_ref, 2018)

# Add GDP to the datasets
sawn["gdp"] = gdp
round_["gdp"] = gdp


def consumption(ds, t):
    """Compute consumption equation 1"""
    return (
        ds["cons_constant"]
        * pow(ds["price"].loc[:, t - 1], ds["cons_price_elasticity"])
        * pow(ds["gdp"].loc[:, t], ds["cons_gdp_elasticity"])
    )


def import_demand(ds, t):
    """Compute import demand equation 4"""
    return (
        ds["imp_constant"]
        * pow(
            ds["price"].loc[:, t - 1] * (1 + ds["tariff"].loc[:, t - 1]),
            ds["imp_price_elasticity"],
        )
        * pow(ds["gdp"].loc[:, t], ds["imp_gdp_elasticity"])
    )


def export_supply(ds, t):
    """Compute export supply equation 7

    Replace negative values by zero."""
    world_imp = ds["imp"].loc[:, t].sum()
    exp = ds["exp_marginal_propensity_to_export"] * world_imp + ds["exp_constant"]
    return np.maximum(exp, 0)


def domestic_production(ds, t):
    """Compute domestic production equation 8
    Replace negative values by zero
    """
    prod = ds["cons"].loc[:, t] + ds["exp"].loc[:, t] - ds["imp"].loc[:, t]
    return np.maximum(prod, 0)


def world_price_indround(ds, ds_other, t):
    """Compute the world price of industrial roundwood equation 9"""
    # TODO: compute the world price of industrial roundwood
    # $G182*($IndroundProd.AJ182^$F182)*($Stock.AJ182^$E182)*EXP($D182*AJ1)
    # ds_round["
    return (
        ds["price_constant"].loc["WORLD"]
        * pow(
            ds["prod"].loc["WORLD", t], ds["price_world_price_elasticity"].loc["WORLD"]
        )
        # *
        # pow(ds_other["stock"].loc[
    )


def world_price(ds, ds_primary, t):
    """Compute the world price equation 10
    as a function of the input price
    """
    return ds["price_constant"].loc["WORLD"] * pow(
        ds_primary["price"].loc["WORLD", t], ds["price_input_elast"].loc["WORLD"]
    )


def local_price(ds, t):
    """Compute the local price equation 12"""
    return ds["price_constant"].loc[COUNTRIES] * pow(
        ds["price"].loc["WORLD", t], ds["price_world_price_elasticity"].loc[COUNTRIES]
    )


# Compute one time step
t = 2019
sawn["cons"].loc[:, t] = consumption(sawn, t)
sawn["imp"].loc[:, t] = import_demand(sawn, t)
sawn["exp"].loc[:, t] = export_supply(sawn, t)
sawn["prod"].loc[:, t] = domestic_production(sawn, t)
sawn["price"].loc["WORLD", t] = world_price(sawn, indround, t)
sawn["price"].loc[COUNTRIES, t] = local_price(sawn, t)

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
sawn_ref_df[["country"] + cols_to_check]


# Plot comparison
# sawn_df["reference"] = "no"
# sawn_ref_df["reference"] = "yes"
# sawn_comp = pandas.concat([sawn_df, sawn_ref_df])
# p = seaborn.scatterplot(x="country", y="prod", hue="reference", data=sawn_comp)
# plt.xticks(rotation=90)
# plt.show()
