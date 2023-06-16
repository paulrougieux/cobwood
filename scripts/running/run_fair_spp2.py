""" Run the pik FAIR and ssp2 scenarios
The purpose of this script is to use the GDP Fair scenario of Bodirsky et al 2022 as an
input to the GFPMx forest sector model

Usage:

    ipython -i ~/repos/cobwood/scripts/running/run_fair_spp2.py

Steps for the run:

1 Load GFPMX data
2 Load GDP Fair scenario data and readjust to the same GDP level as the
  historical series so that there is no discontinuity at the base year.
3 Create a GFPMX object with GFPMx data and GDP Fair data
4 Run the model with that GDP scenario
5 Save output to netcdf files. The GFPMX class should have a method that stores
  each dataset to a scenario output folder  :

    ds.to_netcdf("path/to/file.nc")

- Read the output later to plot the model results, starting with an overview of
  industrial roundwood and fuelwood harvest at EU level

    ds = xarray.open_dataset("path/to/file.nc")

Note: in CBM, the base year is the first year of the simulation, as illustrated
  by the condition `if self.year < self.country.base_year` (in
  `eu_cbm_hat/cbm/dynamic.py`) which governs the start of the harvest allocation
  tool.


"""

import copy
import pandas
import cobwood
from cobwood.gfpmx import GFPMX
from cobwood.gfpmx_data import convert_to_2d_array

gfpmxb2021 = GFPMX(data_dir="gfpmx_base2021", base_year=2021)
# Create deep copies with different GDP scenario
# SSP2 - Bodirstky model
gfpmpikssp2 = copy.deepcopy(gfpmxb2021)
# Degrowth model, PIK FAIR GDP scenario
gfpmpikfair = copy.deepcopy(gfpmxb2021)

# Load GDP data, the country comes from the gfpmx country name
# See the many merges in scripts/load_pik_data.py
gdp_comp = pandas.read_parquet(cobwood.data_dir / "pik" / "gdp_comp.parquet")

selected_sources = [
    "gfpm_gdp_b2021",
    "pik_bau_adjgfpm2021",
    "pik_fair_adjgfpm2021",
    "pik_fair_shift_5",
]

# Prepare PIK GDP so it has country, year and gdp columns
index = ["country", "year"]
column_names = {"pik_bau_adjgfpm2021": "gdp"}
gdp_pik_bau = gdp_comp[index + [*column_names.keys()]].rename(columns=column_names)
column_names = {"pik_fair_adjgfpm2021": "gdp"}
gdp_pik_fair = (
    gdp_comp[index + [*column_names.keys()]]
    .rename(columns=column_names)
    .assign(year=lambda x: x["year"] * 3)
    .pivot(index="country", columns="year", values="gdp")
)

# The GDP added before the run is self.gdp
# In the __init__ method, self.gdp is created from the sheet in wide format.
# self.gdp = convert_to_2d_array(self.data.get_sheet_wide("gdp")).
gfpmxb2021.data["gdp"]
gfpmxb2021.data.get_sheet_wide("gdp")
gfpmxb2021.gdp

convert_to_2d_array(gdp_pik_fair)
