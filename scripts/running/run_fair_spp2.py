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

#######################
# Create GFTMX copies #
#######################
gfpmxb2021 = GFPMX(data_dir="gfpmx_base2021", base_year=2021)
# Create deep copies with different GDP scenario
# SSP2 - Bodirstky model
gfpmxpikbau = copy.deepcopy(gfpmxb2021)
# Degrowth model, PIK FAIR GDP scenario
gfpmxpikfair = copy.deepcopy(gfpmxb2021)

#############################
# Load and prepare GDP data #
#############################
# The country comes from the gfpmx country name
# See the many merges in scripts/load_pik_data.py
gdp_comp = pandas.read_parquet(cobwood.data_dir / "pik" / "gdp_comp.parquet")


def get_gdp_wide(df: pandas.DataFrame, column_name: str, year_min: int = 1995):
    """Transform the given GDP column into wide format for transformation into
    a 2 dimensional data array"""
    index = ["country", "year"]
    return (
        df[index + [column_name]]
        .loc[df["year"] >= year_min]
        .assign(year=lambda x: "value_" + x["year"].astype(str))
        .pivot(index="country", columns="year", values=column_name)
        .reset_index()
    )


pik_fair = get_gdp_wide(gdp_comp, "pik_fair_adjgfpm2021")
pik_bau = get_gdp_wide(gdp_comp, "pik_bau_adjgfpm2021")

# 3 different forms of GDP dataset inside the GFPMX object
# gfpmxb2021.data.get_sheet_wide("gdp")
# gfpmxb2021.data["gdp"]
# gfpmxb2021.gdp

# The GDP added before the run is self.gdp
# In the __init__ method, self.gdp is created from the sheet in wide format.
# self.gdp = convert_to_2d_array(self.data.get_sheet_wide("gdp")).

# Assign new GDP values to the GFTMX objects, reindex them like the existing gdp array
# so that they get empty values for the country aggregates
gfpmxpikbau.gdp = convert_to_2d_array(pik_bau).reindex_like(gfpmxb2021.gdp)
gfpmxpikfair.gdp = convert_to_2d_array(pik_fair).reindex_like(gfpmxb2021.gdp)

# Issue with missing GDP
selector = gfpmxpikfair.gdp.loc[:, 2022].isnull()
print(gfpmxpikfair.gdp["country"][selector])

# selector = pik_fair["country"].str.contains("ina|uyana|ntill")
# pik_fair.loc[selector]
# selector = gdp_comp["country"].str.contains("ina|uyana|ntill")
# gdp_comp.loc[selector].query("year == 2020")
# gdp_comp.query("country_iso == 'CHN'")

# Set values of 'Netherlands Antilles (former)', 'French Guyana',
# To the same as the existing GDP projections in GFPMX 2021
selected_countries = ["Netherlands Antilles (former)", "French Guyana"]
gfpmxpikbau.gdp.loc[selected_countries] = gfpmxb2021.gdp.loc[selected_countries]
gfpmxpikfair.gdp.loc[selected_countries] = gfpmxb2021.gdp.loc[selected_countries]


#######
# Run #
#######
gfpmxpikbau.run()
gfpmxpikfair.run()
