"""This scripts computes all GFPMx equations using xarray

Usage:

    ipython -i ~/repos/gftmx/scripts/compute_all_equations_with_xarray.py

Advantages of using xarray:

    - the shift_index function is not needed any more, we can call
      sawn["price"].loc[:, t - 1] directly.

"""

import numpy as np
from gftmx.gfpmx_data import gfpmx_data
from gftmx.gfpmx_data import convert_to_2d_array

# Load reference data
sawn_ref = gfpmx_data.convert_sheets_to_dataset("sawn")
panel_ref = gfpmx_data.convert_sheets_to_dataset("panel")
gdp = convert_to_2d_array(gfpmx_data.get_sheet_wide("gdp"))

# We will compute demand from the base_year + 1
base_year = 2018

######################################################
# Erase data after base year and copy the data frame #
######################################################
# Using a mask makes the dataset return an error on loc selection
# mask = sawn.coords["year"] > base_year
# sawn = xarray.where(mask, np.nan, sawn_ref).copy()
# sawn["price"].loc[:,t-1]
# # returns KeyError: 2018
# # But selecting the original data works fine
# sawn_ref["price"].loc[:,t-1]
# --> Make a reproducible example and ask on Stackoverflow why this is the case.

sawn = sawn_ref.copy()
sawn["gdp"] = gdp
# Remove values after the base year
for x in sawn.data_vars:
    if len(sawn[x].dims) == 2:
        sawn[x].loc[dict(year=sawn.coords["year"] > base_year)] = np.nan


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
    prod = ds["cons"].loc[:, t] + ds["exp"].loc[:, t] + ds["imp"].loc[:, t]
    return np.maximum(prod, 0)


# Compute one time step
t = 2019
sawn["cons"].loc[:, t] = consumption(sawn, t)
sawn["imp"].loc[:, t] = import_demand(sawn, t)
sawn["exp"].loc[:, t] = export_supply(sawn, t)
sawn["prod"].loc[:, t] = domestic_production(sawn, t)

# # pow(gdp.loc[:,t],)
#
# # Compute world price
#
# # Compute local price
# price_t = (spds["constant"]
#            * pow(spds["price"].loc[:,t-1], spds["elast"])
#           ) # TODO: add gdp elasticity


# Compare computed results to the reference dataset
vars_to_compare = ["cons", "imp", "exp", "prod"]
year = 2019
for var in vars_to_compare:
    np.testing.assert_allclose(sawn[var].loc[:, year], sawn_ref[var].loc[:, year])
