"""
Load PIK-Magpie scenario data from the paper

- Bodirsky, B.L., Chen, D.MC., Weindl, I. et al. Integrating degrowth and efficiency
  perspectives enables an emission-neutral food system by 2100. Nat Food 3, 341–348
  (2022). https://doi.org/10.1038/s43016-022-00500-3

Run this script at the command line with:

    ipython -i ~/repos/cobwood/scripts/load_pik_data.py

See also the associated notebook with comparison plots:

    ../notebooks/explore_pik_gdp_scenarios.md

The data is located at:

- https://zenodo.org/record/5543427#.Y3eYOkjMKcM

The readme says "unit: population: Mio people, gdp: Million USD,"

The data in the figures/scenariogdx folder is in the form of GAMMS GDX files
(although the model interface seems to be in R). There are also csv files in
the figures/incomes folder.


# Mail to Bodirsky

Dear Benjamin Bodirsky,

I enjoyed reading your paper "Integrating degrowth and efficiency perspectives
enables an emission-neutral food system by 2100". I am implementing a forest
sector model which has wood consumption driven by a revenue elasticity of
demand (where revenue is proxied by the GDP). The GFPMx model was published as
"GFPMX: A Cobweb Model of the Global Forest Sector, with an Application to the
Impact of the COVID-19 Pandemic"


I would like to use the GDP projections from your BAU and FAIR GDP scenarios.
Based on the data at https://zenodo.org/record/5543427#.Y3eYOkjMKcM , I
compared the value in DegrowthMAgPIE/figures/incomes/bau_gdp_ppp_iso.csv to
historical GDP values from the World Bank
https://data.worldbank.org/indicator/NY.GDP.MKTP.PP.KD and to values from the
forest sector model GFPMx (also based on the SSP2 storyline). Both other
sources are expressed in constant USD of 2017. See comparison plot attached for
EU countries only. I am wondering why the BAU SSP2 GDP values are almost always
below the world bank values for the historical period. I am also wondering
about the future projection period with the GFPMx model, but I guess I would
have to check

I was trying to look at the FAIR scenario, but it seems that the values in
fair_gdp_ppp_iso.csv do not change much. Do I need to look at the SSP2 column
in that file or at another column?  Where can I look for the GDP projections
used in the FAIR scenario?

Kind regards,
Paul Rougieux


# Reply from co author David M Chen

> "Yes, our GDP units are in constant 2005 USD at market-exchange rate, which
> should explain the consistent difference between them and the World Bank 2017
> values. Our historic GDP values are based on a harmonized dataset (that
> primarily also uses WB as source) documented here, for which we have an updated
> version from 2019.

> And yes for the FAIR scenario, that's a bit unclear, sorry about that, the
> SSP2 column in fair_gdp_ppp_iso.csv has the per capita GDP projections for the
> FAIR scenario. The other columns are the other SSP scenarios as they are (they
> have not been subject to the FAIR redistribution)."

"""
# TODO: update to 2017 constant usd
# Search "world bank change constant USD reference year"

from pathlib import Path
import re

import pandas

# To get country ISO codes
from biotrade.faostat import faostat
from biotrade.world_bank import world_bank

# import gdxpds
import cobwood
from cobwood.gfpmx_data import GFPMXData


country_iso_codes = faostat.country_groups.df[["fao_table_name", "iso3_code"]].rename(
    columns={"fao_table_name": "country", "iso3_code": "country_iso"}
)
# Correct mapping of China and Netherlands to the names used in GFPMX
country_iso_codes = (
    country_iso_codes.query("country != 'China'")  # Remove existing China
    .copy()
    .replace("China, mainland", "China")
    .replace("Netherlands (Kingdom of the)", "Netherlands")
)

# Requires a working version of GAMMS
# dataframes = gdxpds.to_dataframes(magpie_scenario_path / "bau_fulldata.gdx")
# for symbol_name, df in dataframes.items():
#     print("Doing work with {}.".format(symbol_name))

############################
# Load World Bank GDP data #
############################
# Load World Bank GDP, PPP (constant 2017 international $)
# https://data.worldbank.org/indicator/NY.GDP.MKTP.PP.KD
wb_gdp_cst = world_bank.db.select("indicator", indicator_code="NY.GDP.MKTP.PP.KD")
wb_gdp_cst.rename(
    columns={"reporter_code": "country_iso", "value": "wb_gdp_cst"}, inplace=True
)
# Convert from USD to million USD
wb_gdp_cst["wb_gdp_cst"] = wb_gdp_cst["wb_gdp_cst"] / 1e6

# Load World Bank GDP, PPP (current international $)
wb_gdp_cur = world_bank.db.select("indicator", indicator_code="NY.GDP.MKTP.PP.CD")
wb_gdp_cur.rename(
    columns={"reporter_code": "country_iso", "value": "wb_gdp_cur"}, inplace=True
)
# Convert from USD to million USD
wb_gdp_cur["wb_gdp_cur"] = wb_gdp_cur["wb_gdp_cur"] / 1e6

index = ["country_iso", "reporter", "year"]
wb = wb_gdp_cst[index + ["wb_gdp_cst"]].merge(wb_gdp_cur[index + ["wb_gdp_cur"]])

# Check that the constant 2017 USD values correspond to the current value in 2017
# wb["i"] = wb["wb_gdp_cst"]
wb.query("year == 2017 and reporter in @faostat.country_groups.eu_country_names")
# Keep non empty values
wb2017 = wb.query("year == 2017 and wb_gdp_cst == wb_gdp_cst").copy()
# np.testing.assert_allclose(wb2017["wb_gdp_cst"], wb2017["wb_gdp_cur"])
wb2017["diff"] = wb2017["wb_gdp_cst"] - wb2017["wb_gdp_cur"]
wb2017.query("abs(diff) > 1")
# Values are mostly equals except in some special groupings

###############################
# Load PIK Magpie income data #
###############################
scenario_path = Path("~/large_models/DegrowthMAgPIE/figures/scenariogdx")
incomes_path = Path("~/large_models/DegrowthMAgPIE/figures/incomes")


def load_pik_gdp(file_path, new_var_name):
    """Load a pik GDP file and rename the SSP2 column to a new name"""
    df = pandas.read_csv(file_path)
    df.rename(columns=lambda x: re.sub(r" ", "_", str(x)).lower(), inplace=True)
    df.rename(columns={"region": "country_iso", "ssp2": new_var_name}, inplace=True)
    df["year"] = pandas.to_numeric(df["year"].str.replace("y", ""))
    return df


bau_gdp = load_pik_gdp(incomes_path / "bau_gdp_ppp_iso.csv", "pik_bau")
fair_gdp = load_pik_gdp(incomes_path / "fair_gdp_ppp_iso.csv", "pik_fair")


#######################
# Load GFPMX GDP data #
#######################
# Expressed in 1000 USD of 2017

gfpmx_data_b2018 = GFPMXData(data_dir="gfpmx_8_6_2021")
gfpmx_data_b2021 = GFPMXData(data_dir="gfpmx_base2021")


def load_gfpmx_gdp(gfpmx_data: GFPMXData, col_name):
    """Load GFPMX GDP data and give it a column name"""
    df = gfpmx_data.get_sheet_long("gdp").merge(
        country_iso_codes, on="country", how="left"
    )
    # Convert from 1000 USD to million USD
    df["gdp"] = df["gdp"] / 1e3
    df.rename(columns={"gdp": col_name}, inplace=True)
    df.drop(columns="gdp_unnamed_0", inplace=True)
    return df


index = ["country", "country_iso", "year"]
gfpm_gdp = load_gfpmx_gdp(gfpmx_data_b2018, "gfpm_gdp_b2018").merge(
    load_gfpmx_gdp(gfpmx_data_b2021, "gfpm_gdp_b2021"), on=index, how="outer"
)

# Divide
# wb["i"] = wb["wb_gdp_cst"] /
# df['normal'] = df.Value / df['VALUE'].where(df.TIME.str[5:] =='Q1').groupby(df['LOCATION']).transform('first')


# Max GDP per region
bau_gdp.loc[bau_gdp.groupby("country_iso")["pik_bau"].idxmax()]
bau_gdp.query("country_iso=='FRA'")

# Check that there are no NA values for EU country ISO codes
selector = gfpm_gdp["country"].isin(faostat.country_groups.eu_country_names)
assert not any(gfpm_gdp[selector]["country_iso"].isna())


##############################
# Merge data frames together #
##############################
# Merge GFPM, Magpie and world bank data and compare the GDP of EU countries in 2030
index = ["country_iso", "year"]
comp = (
    gfpm_gdp[index + ["country", "gfpm_gdp_b2018", "gfpm_gdp_b2021"]]
    .merge(bau_gdp[index + ["pik_bau"]], on=index, how="left")
    .merge(fair_gdp[index + ["pik_fair"]], on=index, how="left")
    .merge(wb[index + ["wb_gdp_cst", "wb_gdp_cur"]], on=index, how="left")
)

# Reshape to long format
comp_long = comp.melt(
    id_vars=["country_iso", "year", "country"], var_name="source", value_name="gdp"
)

###############################################
# Rescale PIK to a 2017 or a 2021 base year # #
###############################################
#
# https://datahelpdesk.worldbank.org/knowledgebase/articles/114946-how-can-i-rescale-a-series-to-a-different-base-yea
#
# > "For example, you can rescale the 2010 data to 2005 by first creating an index
# > dividing each year of the constant 2010 series by its 2005 value (thus, 2005 will
# > equal 1). Then multiply each year's index result by the corresponding 2005 current
# > U.S. dollar price value."
#
# PIK GDP values are in constant 2005 USD
# Create an index based on the 2017 value

# Convert from 2017 to 2017 values
# - There is no data in 2017, need to interpolate

comp["pik_bau_i"] = comp.groupby("country_iso")["pik_bau"].transform(
    pandas.Series.interpolate, "linear"
)
comp["pik_fair_i"] = comp.groupby("country_iso")["pik_fair"].transform(
    pandas.Series.interpolate, "linear"
)
column_names_2017 = {
    "gfpm_gdp_b2018": "gfpm_gdp_2017",
    "wb_gdp_cur": "wb_gdp_2017",
    "pik_bau_i": "pik_bau_2017",
    "pik_fair_i": "pik_fair_2017",
}
gdp_2017 = (
    comp.loc[comp["year"] == 2017, ["country_iso", *column_names_2017.keys()]]
    .rename(columns=column_names_2017)
    # Remove NA values in country
    .query("country_iso == country_iso")
    .copy()
)
column_names_2021 = {
    "gfpm_gdp_b2021": "gfpm_gdp_2021",
    "pik_bau_i": "pik_bau_2021",
    "pik_fair_i": "pik_fair_2021",
}
gdp_2021 = (
    comp.loc[comp["year"] == 2021, ["country_iso", *column_names_2021.keys()]]
    .rename(columns=column_names_2021)
    .query("country_iso == country_iso")
    .copy()
)

code_continent = faostat.country_groups.df[["iso3_code", "continent"]].rename(
    columns={"iso3_code": "country_iso"}
)
index = ["country_iso", "year"]
gdp_comp = (
    comp.merge(gdp_2017, on="country_iso")
    .merge(gdp_2021, on="country_iso")
    .assign(
        # Scale PIK GDP to World bank GDP 2017
        pik_bau_adjwb2017=lambda x: (x["pik_bau_i"] / x["pik_bau_2017"])
        * x["wb_gdp_2017"],
        pik_fair_adjwb2017=lambda x: (x["pik_fair_i"] / x["pik_fair_2017"])
        * x["wb_gdp_2017"],
        # Scale PIK GDP to GFPMX GDP 2017
        pik_bau_adjgfpm2017=lambda x: (x["pik_bau_i"] / x["pik_bau_2017"])
        * x["gfpm_gdp_2017"],
        pik_fair_adjgfpm2017=lambda x: (x["pik_fair_i"] / x["pik_fair_2017"])
        * x["gfpm_gdp_2017"],
        # Scale PIK GDP to GFPMX GDP 2021
        pik_bau_adjgfpm2021=lambda x: (x["pik_bau_i"] / x["pik_bau_2021"])
        * x["gfpm_gdp_2021"],
        pik_fair_adjgfpm2021=lambda x: (x["pik_fair_i"] / x["pik_fair_2021"])
        * x["gfpm_gdp_2021"],
    )
    .drop(columns=list(column_names_2017.values()) + list(column_names_2021.values()))
    .merge(code_continent, on="country_iso")
)

# Shift by 5 years
gdp_comp["pik_fair_shift_5"] = gdp_comp.groupby("country_iso")[
    "pik_fair_adjgfpm2021"
].shift(periods=5)

# Reshape to long format
index = ["country_iso", "year", "country", "continent"]
gdp_comp_long = gdp_comp.drop(columns=["pik_bau_i", "pik_fair_i"]).melt(
    id_vars=index, var_name="source", value_name="gdp"
)

# See plot comparison between rescaled and original data in the notebook


# Create data frames for EU countries only
selector = comp["country"].isin(faostat.country_groups.eu_country_names)
comp_eu = comp[selector].copy()
selector = comp_long["country"].isin(faostat.country_groups.eu_country_names)
comp_eu_long = comp_long[selector].copy()

# Check that the PIK constant 2005 USD values correspond to WB current value in 2005
comp_eu_2005 = comp_eu.query("year == 2005 and pik_bau == pik_bau")


############################################
# Rescale using the rate of growth instead #
############################################
# What countries are available and how does is the fair redistribution implemented?
# For each country compute the proportion decrease between 2020 and 2030.


###################################################
# Keep only selected year for comparison purposes #
###################################################
eu_countries = faostat.country_groups.eu_country_names
gdp_comp_eu = gdp_comp.query("country in @faostat.country_groups.eu_country_names")
# Keep only ssp2 and adjusted pik fair scenario
# Keep country iso to check we only have EU countries
agg = {"country_iso": lambda x: "".join(x.unique()), "gdp": "sum"}
gdp_comp_long_agg_eu_2 = (
    gdp_comp.melt(
        id_vars=["country_iso", "year", "country", "continent"],
        var_name="source",
        value_name="gdp",
    )
    .query("country in @eu_countries")
    .groupby(["year", "source"])
    .agg(agg)
    .reset_index()
    # TODO: fix this in a more elegant way
    .query("gdp>0.1")
    .copy()
)
print(gdp_comp_long_agg_eu_2["country_iso"].unique())
gdp_comp_long_agg_eu_2.value_counts(["source", "country_iso"])

####################
# Aggregate EU GDP #
####################
# For a summary table in the technical report
selected_sources = ["gfpm_gdp_b2021", "pik_fair_adjgfpm2021", "pik_bau_adjgfpm2021"]
selected_years = [1992, 2000, 2010, 2020, 2030, 2050, 2070]
gdp_comp_eu_selected = (
    gdp_comp_long_agg_eu_2
    # Convert from million USD to billion USD
    .assign(gdp_bil=lambda x: x["gdp"] / 1e3)
    .query("year in @selected_years and source in @selected_sources")
    .pivot(index="source", columns="year", values="gdp_bil")
)
# Year 1992 is only available in GFPM base 2018
# Compare GFPM GDP base 2018 and base 2021
gdp_b2018_b2021 = (
    gdp_comp_long_agg_eu_2.query("source in ['gfpm_gdp_b2018', 'gfpm_gdp_b2021']")
    # Keep this index on year please it is needed for the plot and the loc selection
    .pivot(columns="source", index="year", values="gdp")
)
# Linear interpolation of 1992
gdp_b2018_b2021["gfpm_gdp_b2021_i"] = gdp_b2018_b2021["gfpm_gdp_b2021"].interpolate(
    method="linear", limit_direction="both"
)
# gdp_b2018_b2021.plot()
gdp_comp_eu_selected.loc["gfpm_gdp_b2021", "1992"] = (
    float(gdp_b2018_b2021.loc[1992, "gfpm_gdp_b2021_i"]) / 1e3
)


gdp_comp_eu_selected.round().to_csv("/tmp/gdp_comp_eu_selected.csv")

# Use a simple ratio to compute back GFPM GDP 1992 from GFPMx GDP b 2018
gdp_comp_long_agg_eu_2.query("year in [1992, 2000]")


#####################
# Store output data #
#####################
pik_data_dir = cobwood.create_data_dir("pik")

# Write EU GDP to a parquet file
(
    # Remove interpolated data
    comp_eu.drop(columns=["pik_bau_i", "pik_fair_i"]).to_parquet(
        pik_data_dir / "comp_eu.parquet"
    )
)

# Write GDP comparison to a parquet file
gdp_comp.to_parquet(pik_data_dir / "gdp_comp.parquet")

# Write to a compressed csv file
compression_opts = dict(method="zip", archive_name="comp.csv")
(
    comp.drop(columns=["pik_bau_i", "pik_fair_i"]).to_csv(  # Remove interpolated data
        "/tmp/comp.csv.zip", index=False, compression=compression_opts
    )
)
