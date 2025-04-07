""" Run the pik FAIR and ssp2 scenarios The purpose of this script is to use
the GDP Fair scenario of Bodirsky et al 2022 as an input to the GFPMx forest
sector model

Usage:

    ipython -i ~/repos/cobwood/scripts/running/run_fair_spp2.py

Dependency this script should be run to prepare the PIK GDP data:

    ipython -i ~/repos/cobwood/scripts/load_pik_data.py

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
import pandas
import cobwood
from cobwood.gfpmx import GFPMX
from cobwood.gfpmx_data import convert_to_2d_array
from cobwood.gfpmx_equations import compute_country_aggregates
from biotrade.faostat import faostat  # only for an EU diagnostic plot

eu_cbm_data_dir = cobwood.data_dir.parent / "eu_cbm" / "eu_cbm_data"

##############################
# Create GFTMX model objects #
##############################
print("Create GFTMX model objects.")
msg = "Do you want to erase output and re-run the scenarios?"
if input(msg + "\nPlease confirm [y/n]:") != "y":
    raise ValueError("Cancelled.")

gfpmxb2021 = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario="base_2021", rerun=True
)
# BAU SSP2 GDP projections from Bodirstky et al 2022
gfpmxpikssp2 = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario="pikssp2", rerun=True
)
# FAIR GDP projections from Bodirstky et al 2022
gfpmxpikfair = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario="pikfair", rerun=True
)
# Scenario for a fuel wood demand elasticity of 1 fel1
gfpmxpikfair_fel1 = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario="pikfair_fel1", rerun=True
)
gfpmxpikssp2_fel1 = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario="pikssp2_fel1", rerun=True
)


# Models that will be run here and transmitted for further processing to CBM
models = [
    gfpmxpikssp2,
    gfpmxpikfair,
    gfpmxpikssp2_fel1,
    gfpmxpikfair_fel1,
]


#######################################################
# Re-compute the aggregates for the historical period #
#######################################################
# There seems to be an issue in the GFPMX spreadsheet where some continents get
# inverted
print("Re-compute aggregates for the historical period.")
for model in models + [gfpmxb2021]:
    for this_product in model.products:
        for year in range(1995, 2022):
            compute_country_aggregates(model[this_product], year)
            compute_country_aggregates(model.other, year, ["area", "stock"])


#############################
# Load and prepare GDP data #
#############################
print("Prepare GDP data")
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
# This is the place where we rename PIK BAU to PIK SSP2, because BAU has a
# different meaning in the forest dynamics scenarios (it means the business as
# usual in terms of other wood components removals)
pik_ssp2 = get_gdp_wide(gdp_comp, "pik_bau_adjgfpm2021")

# 3 different forms of GDP dataset inside the GFPMX object
# gfpmxb2021.data.get_sheet_wide("gdp")
# gfpmxb2021.data["gdp"]
# gfpmxb2021.gdp

# The GDP added before the run is self.gdp
# In the __init__ method, self.gdp is created from the sheet in wide format.
# self.gdp = convert_to_2d_array(self.data.get_sheet_wide("gdp")).

# Assign new GDP values to the GFTMX objects, reindex them like the existing gdp array
# so that they get empty values for the country aggregates
# Convert from million USD to 1000 USD
gfpmxpikssp2.gdp = convert_to_2d_array(pik_ssp2).reindex_like(gfpmxb2021.gdp) * 1e3
gfpmxpikfair.gdp = convert_to_2d_array(pik_fair).reindex_like(gfpmxb2021.gdp) * 1e3

# GDP diagnostic plot
df = pik_fair.set_index("country").transpose()
eu_countries = faostat.country_groups.eu_country_names
cols = [col for col in df.columns if col in eu_countries]
# df[cols].plot()
selector = df.index.str.contains("1990|2020|2050")
# Relative difference
df.loc[selector, cols].diff() / df.loc[selector, cols]
df.loc[selector, cols].sum(axis=1).diff() / df.loc[selector, cols].sum(axis=1)


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
gfpmxpikssp2.gdp.loc[selected_countries] = gfpmxb2021.gdp.loc[selected_countries]
gfpmxpikfair.gdp.loc[selected_countries] = gfpmxb2021.gdp.loc[selected_countries]

# Missing PIK GDP for China (CHN) and Netherlands (NLD)
# The ISO 3 codes are present in the PIK csv files, why do they get dropped?


# Assign fuelwood elasticities 1 scenarios the same GDP as the other fair and bau
gfpmxpikssp2_fel1.gdp = gfpmxpikssp2.gdp
gfpmxpikfair_fel1.gdp = gfpmxpikfair.gdp


########################################
# Change fuel wood demand elasticities #
########################################
# Change fuel wood demand elasticities to 1
gfpmxpikfair_fel1.fuel["cons_gdp_elasticity"].loc[gfpmxpikfair_fel1.fuel.c] = 1
gfpmxpikssp2_fel1.fuel["cons_gdp_elasticity"].loc[gfpmxpikssp2_fel1.fuel.c] = 1


def cons_constant(ds, t):
    """Compute back the constant given the historical consumption"""
    return ds["cons"].loc[ds.c, t] / (
        pow(ds["price"].loc[ds.c, t - 1], ds["cons_price_elasticity"])
        * pow(ds["gdp"].loc[ds.c, t], ds["cons_gdp_elasticity"])
    )


# Add GDP projections to secondary products datasets.
gfpmxpikfair_fel1.fuel["gdp"] = gfpmxpikfair_fel1.gdp
gfpmxpikssp2_fel1.fuel["gdp"] = gfpmxpikssp2_fel1.gdp

# Calibrate the constant so that it reproduces the value in 2021
gfpmxpikfair_fel1.fuel["cons_constant"].loc[gfpmxpikfair_fel1.fuel.c] = cons_constant(
    gfpmxpikfair_fel1.fuel, 2021
)
gfpmxpikssp2_fel1.fuel["cons_constant"].loc[gfpmxpikssp2_fel1.fuel.c] = cons_constant(
    gfpmxpikssp2_fel1.fuel, 2021
)

# gfpmxpikfair_fel1.fuel["cons_constant"].to_pandas().reset_index().query("country in ['Germany','France']")
# cons_constant(gfpmxpikfair_fel1.fuel,2021).to_pandas().reset_index().query("country in ['Germany','France']")


##################################################################
# Fix Czechia's high propensity to export due to Salvage logging #
##################################################################
# Between 2016 and 2021, there was a massive bark beetle attack followed by
# salvage logging that represents several times the yearly harvest and large
# amounts of exports. Looking at Czechia's consumption, production and trade of
# all products
#     >>> products = ["sawn", "panel", "fuel", "paper", "indround", "pulp"]
#     >>> ds_fair = [gfpmxpikfair[x] for x in products]
#     >>> for ds in df_fair:
#     >>>     facet_plot_by_var(ds, countries=["Czechia"])
# The scenario should reduce industrial roundwood and sawnwood exports for the period
# To a value that corresponds to the average 2015-2020
# This can be achieved by reducing the marginal propensity to export.


selected_scenarios = [gfpmxpikssp2_fel1, gfpmxpikfair_fel1]
# Estimates from cobwood/scripts/estimating/estimate_export_supply.py
for scenario in selected_scenarios:
    scenario["indround"]["exp_constant"].loc["Czechia"] = -395.63598204559366
    scenario["indround"]["exp_marginal_propensity_to_export"].loc[
        "Czechia"
    ] = 0.030772674789748013
    scenario["sawn"]["exp_constant"].loc["Czechia"] = 1344.7487441529158
    scenario["sawn"]["exp_marginal_propensity_to_export"].loc[
        "Czechia"
    ] = 0.0025397644268203446

# See plots in notebook


# # Check resulting export values
# from cobwood.gfpmx_equations import export_supply
# export_supply(gfpmxpikssp2_fel1["indround"], 2021).loc["Czechia"]
# export_supply(gfpmxpikssp2["indround"], 2021).loc["Czechia"]


# for scenario in selected_scenarios:
#     product = "indround"
#     file_name = f"/tmp/{scenario.scenario}_{product}.csv"
#     scenario[product].to_dataframe().loc[["WORLD", "Czechia"]].to_csv(file_name)


#######
# Run #
#######
for model in models + [gfpmxb2021]:
    model.run()


# Note: this loop could be vectorized on years to speed it up.


####################
# Save output data #
####################
# print("Save output data to CSV")
# Note: the model run instruction already saves the output in NetCDF files
# under cobwood_data/gfpmx_output
#

# Save output to csv files in cobwood_data
# print("Save output to csv")
# gfpmxpikfair.datasets
# A dictionary of datasets which we can use to loop or store results
# fair_dir = cobwood.create_data_dir("pikfair")
# for ds in [
#     gfpmxpikfair.indround,
#     gfpmxpikfair.sawn,
#     gfpmxpikfair.panel,
#     gfpmxpikfair.pulp,
#     gfpmxpikfair.paper,
#     gfpmxpikfair.fuel,
#     gfpmxpikfair.other,
# ]:
#     # If a data array is 2 dimensional, write it to disk
#     for this_var in ds.data_vars:
#         if ds[this_var].ndim == 2:
#             df = ds[this_var].to_pandas()
#             df.rename(columns=lambda x: "value_" + str(x), inplace=True)
#             df.reset_index(inplace=True)
#             file_name = ds.product + this_var + ".csv"
#             df.to_csv(fair_dir / file_name, index=False)
#             print(file_name, "\n", df.columns[[0, 1, -1]], "\n")


###################################
# Save output data to eu_cbm_data #
###################################
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
    print(f"Writing {df.shape[0]} rows and {df.shape[1]} columns to:")
    print("  ", file_path, "\n")


def save_harvest_demand_to_eu_cbm_hat(model):
    """Save harvest demand to eu_cbm_hat"""
    eu_cbm_harvest_dir = pathlib.Path(eu_cbm_data_dir) / "domestic_harvest"
    eu_cbm_harvest_dir = eu_cbm_harvest_dir / model.scenario
    eu_cbm_harvest_dir.mkdir(exist_ok=True)
    da_to_csv(
        model.indround["prod"],
        eu_cbm_harvest_dir / "irw_harvest.csv",
        "Industrial roundwood",
    )
    da_to_csv(model.fuel["prod"], eu_cbm_harvest_dir / "fw_harvest.csv", "Fuelwood")


for model in models:
    save_harvest_demand_to_eu_cbm_hat(model)
