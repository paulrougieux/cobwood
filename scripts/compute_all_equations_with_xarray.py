"""This scripts computes all GFPMx equations using xarray

Usage:

    ipython -i ~/repos/gftmx/scripts/compute_all_equations_with_xarray.py

Advantages of using xarray:

- the shift_index function is not needed any more, we can call
  sawn["price"].loc[:, t - 1] directly.

"""

import numpy as np

# import pandas
# import seaborn

from gftmx.gfpmx_data import gfpmx_data
from gftmx.gfpmx_data import convert_to_2d_array

# Load reference data
sawn_ref = gfpmx_data.convert_sheets_to_dataset("sawn")
round_ref = gfpmx_data.convert_sheets_to_dataset("round")
panel_ref = gfpmx_data.convert_sheets_to_dataset("panel")
gdp = convert_to_2d_array(gfpmx_data.get_sheet_wide("gdp"))


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
round_ref2 = round_ref.copy()


def remove_values_after_the_base_year(ds, base_year):
    """Remove values after the base year and return a deep copy of the
    input dataset, i.e. the input dataset is not modified in this case.
    """
    ds_out = ds.copy(deep=True)
    for x in ds_out.data_vars:
        if len(ds_out[x].dims) == 2:
            ds_out[x].loc[dict(year=ds_out.coords["year"] > base_year)] = np.nan
    return ds_out


sawn = remove_values_after_the_base_year(sawn_ref, 2018)
# Use and underscore in order not to overwrite the round() function
round_ = remove_values_after_the_base_year(round_ref, 2018)
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


def world_price(ds, ds_primary, t):
    """Compute the world price equation 10
    as a function of the input price
    """
    return ds["price_constant"].loc["WORLD"] * pow(
        ds_primary["price"].loc["WORLD", t], ds["price_input_elast"].loc["WORLD"]
    )


# Compute one time step
t = 2019
sawn["cons"].loc[:, t] = consumption(sawn, t)
sawn["imp"].loc[:, t] = import_demand(sawn, t)
sawn["exp"].loc[:, t] = export_supply(sawn, t)
sawn["prod"].loc[:, t] = domestic_production(sawn, t)
sawn["price"].loc["WORLD", t] = world_price(sawn, round_, t)

# Compare computed results to the reference dataset
vars_to_compare = ["cons", "imp", "exp", "prod"]
country_aggregates = [
    "WORLD",
    "AFRICA",
    "NORTH AMERICA",
    "SOUTH AMERICA",
    "ASIA",
    "OCEANIA",
    "EUROPE",
]
countries_only = sawn.country[~sawn.country.isin(country_aggregates)]
year = 2019
for var in vars_to_compare:
    print(f"Checking {var}")
    np.testing.assert_allclose(
        sawn[var].loc[countries_only, year],
        sawn_ref[var].loc[countries_only, year],
        rtol=1e-3,
    )

# Comparison in case of mismatch
sawn_df = sawn.loc[dict(country=countries_only, year=year)].to_pandas().reset_index()
sawn_ref_df = (
    sawn_ref.loc[dict(country=countries_only, year=year)].to_pandas().reset_index()
)
cols_to_check = ["cons", "imp", "exp", "prod"]
print(sawn_df[cols_to_check])
print(sawn_ref_df[cols_to_check])
sawn_df["prod_diff"] = sawn_df["prod"] / sawn_ref_df["prod"] - 1
sawn_df["cons_diff"] = sawn_df["cons"] / sawn_ref_df["cons"] - 1
print(sawn_df[["cons_diff", "prod_diff"]].describe())

# Plot comparison
# sawn_df["reference"] = "no"
# sawn_ref_df["reference"] = "yes"
# sawn_comp = pandas.concat([sawn_df, sawn_ref_df])
# p = seaborn.scatterplot(x="country", y="prod", hue="reference", data=sawn_comp)
# plt.xticks(rotation=90)
# plt.show()
