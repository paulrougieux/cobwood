"""This scripts computes all GFPMx equations using xarray
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

sawn = sawn_ref.copy()
for x in sawn.data_vars:
    if len(sawn[x].dims) == 2:
        sawn[x].loc[dict(year=sawn.coords["year"] > base_year)] = np.nan


# Compute consumption equation 1
t = 2019
# da[dict(space=0)] = 0
sawn["cons"][dict(year=t)] = (
    sawn["cons_constant"]
    * pow(sawn["price"].loc[:, t - 1], sawn["cons_price_elasticity"])
    * pow(gdp.loc[:, t], sawn["cons_gdp_elasticity"])
)

# # pow(gdp.loc[:,t],)
#
# # Compute world price
#
# # Compute local price
# price_t = (spds["constant"]
#            * pow(spds["price"].loc[:,t-1], spds["elast"])
#           ) # TODO: add gdp elasticity


# Compare
np.testing.assert_allclose(sawn["price"].loc[:, 2018], sawn_ref["price"].loc[:, 2018])
