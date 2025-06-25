"""Explore the output of the Fair and SSP2 scenarios

Before you can explore scenario output, you should run the model first with
this script:

    scripts/running/run_fair_spp2.py

Then this script can load the output in NetCDF files to explore the scenario data.


See also:

- the `save_harvest_demand_to_eu_cbm_hat` function used to send cobwood output
  data to EU-CBM-HAT at the end of the running script.

- data preparation script for the CBM output data of the SSP2 FAIR paper
    ~/eu_cbm/eu_cbm_explore/scenarios/ssp2_fair_degrowth/ssp2_fair_owc_prepare_data.py


"""

import pandas
from cobwood.gfpmx import GFPMX

###########################################
# Load data without re-running the model. #
###########################################
gfpmxpikfair_fel1 = GFPMX(scenario="pikfair_fel1")
gfpmxpikssp2_fel1 = GFPMX(scenario="pikssp2_fel1")
gfpmxpikssp2 = GFPMX(scenario="pikssp2")

# Get irw and fw production data for the ssp2 and ssp2_fel1 scenarios
ssp2_fel1_prod = gfpmxpikssp2_fel1.get_df(product=["indround", "fuel"], var="prod")
ssp2_prod = gfpmxpikssp2.get_df(product=["indround", "fuel"], var="prod")
prod = pandas.concat([ssp2_fel1_prod, ssp2_prod]).reset_index()

# Create a multi-level column structure
prod_grouped = prod.set_index(["country", "year", "scenario"])[
    ["fuel_prod", "indround_prod"]
]
# Unstack the scenario level to create columns
prod_wide2 = prod_grouped.unstack("scenario")

# Convert from 1000 M3 to M3
print("Production units are expressed in", gfpmxpikssp2["indround"]["prod"].unit)
prod_wide2 = prod_wide2 * 1e3

# Flatten the column names to get format like 'fuel_prod_pikssp2'
prod_wide2.columns = [f"{col[0]}_{col[1]}" for col in prod_wide2.columns]
prod_wide2 = prod_wide2.reset_index()

# Display a data Array for countries only
fairsawn = gfpmxpikfair_fel1["sawn"]
print(fairsawn["cons"][fairsawn.c])
