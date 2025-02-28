"""Explore the output of the Fair and SSP2 scenarios

The run script should run first:

    scripts/running/run_fair_spp2.py

Then this script can load the output in NetCDF files to explore the scenario data.

"""


# Load data without re-running the model.
from cobwood.gfpmx import GFPMX

# Scenario for a fuel wood demand elasticity of 1 fel1
gfpmxpikfair_fel1 = GFPMX(
    input_dir="gfpmx_base2021",
    base_year=2021,
    scenario_name="pikfair_fel1",
    rerun=False,
)
gfpmxpikssp2_fel1 = GFPMX(
    input_dir="gfpmx_base2021",
    base_year=2021,
    scenario_name="pikssp2_fel1",
    rerun=False,
)


# Display a data Array for countries only
fairsawn = gfpmxpikfair_fel1["sawn"]
print(fairsawn["cons"][fairsawn.c])
