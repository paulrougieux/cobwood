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

import pathlib
import copy
import pandas
import cobwood
from cobwood.gfpmx import GFPMX
from cobwood.gfpmx_data import convert_to_2d_array
from cobwood.gfpmx_equations import compute_country_aggregates
from eu_cbm_hat import eu_cbm_data_dir

#######################
# Create GFTMX copies #
#######################
gfpmxb2021 = GFPMX(data_dir="gfpmx_base2021", base_year=2021)
# Create deep copies with different GDP scenario
# BAU SSP2 GDP projections from Bodirstky et al 2022
gfpmxpikbau = copy.deepcopy(gfpmxb2021)
# FAIR GDP projections from Bodirstky et al 2022
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
# so that they get empty values for the country aggregatesgfpmxb2021
# Convert from million USD to 1000 USD
gfpmxpikbau.gdp = convert_to_2d_array(pik_bau).reindex_like(gfpmxb2021.gdp) * 1e3
gfpmxpikfair.gdp = convert_to_2d_array(pik_fair).reindex_like(gfpmxb2021.gdp) * 1e3

# Issue with missing GDP
# selector = gfpmxpikfair.gdp.loc[:, 2022].isnull()
# print(gfpmxpikfair.gdp["country"][selector])

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
gfpmxpikbau.last_time_step = 2070
gfpmxpikfair.last_time_step = 2070
gfpmxpikbau.run()
gfpmxpikfair.run()

# Re-compute the aggregates for the historical period
# There seems to be an issue in the GFPMX spreadsheet where some continents get
# inverted

for year in range(1995, 2022):
    compute_country_aggregates(gfpmxpikbau.indround, year)
    compute_country_aggregates(gfpmxpikfair.indround, year)
    compute_country_aggregates(gfpmxpikbau.fuel, year)
    compute_country_aggregates(gfpmxpikfair.fuel, year)
    compute_country_aggregates(gfpmxpikbau.sawn, year)
    compute_country_aggregates(gfpmxpikfair.sawn, year)
    compute_country_aggregates(gfpmxpikbau.panel, year)
    compute_country_aggregates(gfpmxpikfair.panel, year)
    compute_country_aggregates(gfpmxpikbau.paper, year)
    compute_country_aggregates(gfpmxpikfair.paper, year)
    compute_country_aggregates(gfpmxpikbau.pulp, year)
    compute_country_aggregates(gfpmxpikfair.pulp, year)
    compute_country_aggregates(gfpmxpikbau.other, year, ["area", "stock"])
    compute_country_aggregates(gfpmxpikfair.other, year, ["area", "stock"])

############################################
# Save output to csv files in cobwood_data #
############################################
# gfpmxpikfair.datasets
# A dictionary of datasets which we can use to loop or store results
fair_dir = cobwood.create_data_dir("pikfair")
for ds in [
    gfpmxpikfair.indround,
    gfpmxpikfair.sawn,
    gfpmxpikfair.panel,
    gfpmxpikfair.pulp,
    gfpmxpikfair.paper,
    gfpmxpikfair.fuel,
    gfpmxpikfair.other,
]:
    # If a data array is 2 dimensional, write it to disk
    for this_var in ds.data_vars:
        if ds[this_var].ndim == 2:
            df = ds[this_var].to_pandas()
            df.rename(columns=lambda x: "value_" + str(x), inplace=True)
            df.reset_index(inplace=True)
            file_name = ds.product + this_var + ".csv"
            df.to_csv(fair_dir / file_name, index=False)
            print(file_name, "\n", df.columns[[0, 1, -1]], "\n")


##############################
# Save output to eu_cbm_data #
##############################
def da_to_csv(da, file_path, faostat_name):
    """Data set to eu_cbm_data csv file"""
    df = da.to_pandas()
    df.rename(columns=lambda x: "value_" + str(x), inplace=True)
    df.reset_index(inplace=True)
    # Add columns required by eu_cbm_hat
    df["faostat_name"] = faostat_name
    df["element"] = "Production"
    df["unit"] = "1000m3"
    # Place the last 3 columns first
    cols = list(df.columns)
    cols = cols[-3:] + cols[:-3]
    df = df[cols]
    # Write to CSV
    df.to_csv(file_path, index=False)
    print(df.head(2))
    print(file_path, "\n", df.columns[[0, 1, -1]], "\n")


# PIK Fair
eu_cbm_fair_dir = pathlib.Path(eu_cbm_data_dir) / "domestic_harvest" / "pikfair"
eu_cbm_fair_dir.mkdir(exist_ok=True)
da_to_csv(
    gfpmxpikfair.indround["prod"],
    eu_cbm_fair_dir / "irw_harvest.csv",
    "Industrial roundwood",
)
da_to_csv(gfpmxpikfair.fuel["prod"], eu_cbm_fair_dir / "fw_harvest.csv", "Fuelwood")

# PIK Bau
eu_cbm_bau_dir = pathlib.Path(eu_cbm_data_dir) / "domestic_harvest" / "pikbau"
eu_cbm_bau_dir.mkdir(exist_ok=True)
da_to_csv(
    gfpmxpikbau.indround["prod"],
    eu_cbm_bau_dir / "irw_harvest.csv",
    "Industrial roundwood",
)
da_to_csv(gfpmxpikbau.fuel["prod"], eu_cbm_bau_dir / "fw_harvest.csv", "Fuelwood")
