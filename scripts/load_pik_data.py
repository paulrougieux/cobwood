"""
Load PIK-Magpie scenario data from the paper

- Bodirsky, B.L., Chen, D.MC., Weindl, I. et al. Integrating degrowth and efficiency
  perspectives enables an emission-neutral food system by 2100. Nat Food 3, 341–348
  (2022). https://doi.org/10.1038/s43016-022-00500-3

Run this script at the command line with:

    ipython -i ~/repos/gftmx/scripts/load_pik_data.py

See comparison plots in the notebook:

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

from pathlib import Path
import numpy as np
import pandas
import matplotlib.pyplot as plt
import seaborn

# import gdxpds
from gftmx.gfpmx_data import gfpmx_data

# To get country ISO codes
from biotrade.faostat import faostat
from biotrade.world_bank import world_bank
import re

country_iso_codes = faostat.country_groups.df[["fao_table_name", "iso3_code"]].rename(
    columns={"fao_table_name": "country", "iso3_code": "country_iso"}
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
gfpm_gdp = gfpmx_data.get_sheet_long("gdp").merge(
    country_iso_codes, on="country", how="left"
)
# Convert from 1000 USD to million USD
gfpm_gdp["gdp"] = gfpm_gdp["gdp"] / 1e3
gfpm_gdp.rename(columns={"gdp": "gfpm_gdp"}, inplace=True)

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
    gfpm_gdp[index + ["country", "gfpm_gdp"]]
    .merge(bau_gdp[index + ["pik_bau"]], on=index, how="left")
    .merge(fair_gdp[index + ["pik_fair"]], on=index, how="left")
    .merge(wb[index + ["wb_gdp_cst", "wb_gdp_cur"]], on=index, how="left")
)

# Reshape to long format
comp_long = comp.melt(
    id_vars=["country_iso", "year", "country"], var_name="source", value_name="gdp"
)

###################################
# Rescale PIK to a 2017 base year #
###################################
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
bau_gdp_2017 = (
    comp.loc[comp["year"] == 2017, ["country_iso", "pik_bau_i"]]
    .rename(columns={"pik_bau_i": "pik_bau_2017"})
    # Remove NA values in country
    .query("country_iso == country_iso")
    .copy()
)
wb_gdp_2017 = (
    comp.loc[comp["year"] == 2017, ["country_iso", "wb_gdp_cur"]]
    .rename(columns={"wb_gdp_cur": "wb_gdp_2017"})
    # Remove NA values in country # Todo: fix this at another level
    .query("country_iso == country_iso")
    .copy()
)

index = ["country_iso", "year"]
comp2 = (
    comp.merge(bau_gdp_2017, on="country_iso")  # [index + ["pik_bau_i"]]
    .merge(wb_gdp_2017, on="country_iso")
    # Scale to one in 2017
    # .assign(pik_bau_scale_2017 = lambda x: x["pik_bau_i"] / x["pik_bau_2017"])
    # Multiply by the current value in 2017
    .assign(
        pik_bau_adj2017=lambda x: (x["pik_bau_i"] / x["pik_bau_2017"])
        * x["wb_gdp_2017"]
    )
    .drop(columns=["pik_bau_2017", "wb_gdp_2017"])
)

#   # Join 2017 constant values from the world bank
#   .merge(wb[index + ["wb_gdp_cst"]], on=index, how="left")
#   )


# Reshape to long format
comp2_long = comp2.drop(columns=["pik_bau_i", "pik_fair_i"]).melt(
    id_vars=["country_iso", "year", "country"], var_name="source", value_name="gdp"
)

# Now use 2017 constant GDP as a new reference value
# compute forward
# compute backward

# TODO plot comparison between rescaled and original data


# Create data frames for EU countries only
selector = comp["country"].isin(faostat.country_groups.eu_country_names)
comp_eu = comp[selector].copy()
selector = comp_long["country"].isin(faostat.country_groups.eu_country_names)
comp_eu_long = comp_long[selector].copy()

# Check that the PIK constant 2005 USD values correspond to WB current value in 2005
comp_eu_2005 = comp_eu.query("year == 2005 and pik_bau == pik_bau")

# Write to parquet files

# TODO: move these plots to the notebook
# TODO: update to 2017 constant usd
# Search "world bank change constant usd reference year"


#######################
# XY comparison plots #
#######################
# Compare PIK BAU to GFTMx GDP scenario
comp_eu["country"] = comp_eu["country"].astype("category")
g = seaborn.FacetGrid(
    comp_eu.query("not pik_bau.isna()"),
    col="country",
    col_wrap=6,
    sharex=False,
    sharey=False,
)  # , height=6)
g.map_dataframe(seaborn.scatterplot, x="gfpm_gdp", y="pik_bau", hue="country")
# From https://stackoverflow.com/questions/54390054/how-to-add-a-comparison-line-to-all-plots-when-using-seaborns-facetgrid


def const_line(*args, **kwargs):
    x = np.arange(0, 1e7, 1e6)
    plt.plot(x, x)


g.map(const_line)
plt.show()


#################################
# X along time comparison plots #
#################################
# GDP in billion USD
comp_eu_long["gdp_b"] = comp_eu_long["gdp"] / 1e3
g = seaborn.relplot(
    data=comp_eu_long,
    x="year",
    y="gdp_b",
    col="country",
    col_wrap=7,
    hue="source",
    style="source",
    kind="line",
    height=3,
    facet_kws={"sharey": False, "sharex": False},
)
g.fig.supylabel("GDP in billion USD")
g.fig.subplots_adjust(left=0.05)
g.set(ylim=(0, None))
plt.savefig("/tmp/comp_gdp_by_country.pdf")
# plt.savefig("/tmp/comp_gdp_by_country.png")

# With rescaled values
eu_countries = faostat.country_groups.eu_country_names
comp2_long["gdp_b"] = comp2_long["gdp"] / 1e3
g = seaborn.relplot(
    data=comp2_long.query("country in @eu_countries"),
    x="year",
    y="gdp_b",
    col="country",
    col_wrap=7,
    hue="source",
    style="source",
    kind="line",
    height=3,
    facet_kws={"sharey": False, "sharex": False},
)
g.fig.supylabel("GDP in billion USD")
g.fig.subplots_adjust(left=0.05)
g.set(ylim=(0, None))
plt.savefig("/tmp/comp_gdp_by_country_rescaled.pdf")
# plt.savefig("/tmp/comp_gdp_by_country.png")


# Whole EU
comp_eu_long_agg = (
    comp_eu_long.groupby(["year", "source"])
    .agg(sum)
    .reset_index()
    # TODO: fix this in a more elegant way
    .query("gdp>0.1")
    .copy()
)

selected_sources = ["gfpm_gdp", "pik_bau", "pik_fair"]
p = seaborn.lineplot(
    x="year",
    y="gdp_b",
    hue="source",
    data=comp_eu_long_agg.query("source in @selected_sources"),
)
p.set(ylabel="GDP in billion USD", title="EU GDP scenarios")
# plt.show()
plt.savefig("/tmp/comp_gdp_eu_aggregate.png")

# Convert to 2017 USD
# Compute index on 2005 value
comp_eu_long


# Compute yearly increase by variable
