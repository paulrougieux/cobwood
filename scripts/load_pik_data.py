"""
Load PIK-Magpie scenario data from the paper

- Bodirsky, B.L., Chen, D.MC., Weindl, I. et al. Integrating degrowth and efficiency
  perspectives enables an emission-neutral food system by 2100. Nat Food 3, 341–348
  (2022). https://doi.org/10.1038/s43016-022-00500-3

The data is located at:

- https://zenodo.org/record/5543427#.Y3eYOkjMKcM

The readme says "unit: population: Mio people, gdp: Million USD,"

The data in the figures/scenariogdx folder is in the form of GAMMS GDX files
(although the model interface seems to be in R). There are also csv files in
the figures/incomes folder.

Run this script at the command line with

    ipython -i ~/repos/gftmx/scripts/load_pik_data.py

# Draft mail to Bodirsky

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

# Load Magpie income data
scenario_path = Path("~/large_models/DegrowthMAgPIE/figures/scenariogdx")
incomes_path = Path("~/large_models/DegrowthMAgPIE/figures/incomes")
bau_gdp = pandas.read_csv(incomes_path / "bau_gdp_ppp_iso.csv")
bau_gdp.rename(columns=lambda x: re.sub(r" ", "_", str(x)).lower(), inplace=True)
bau_gdp.rename(columns={"region": "country_iso"}, inplace=True)
bau_gdp["year"] = pandas.to_numeric(bau_gdp["year"].str.replace("y", ""))

fair_gdp = pandas.read_csv(incomes_path / "fair_gdp_ppp_iso.csv")
fair_gdp.rename(columns=lambda x: re.sub(r" ", "_", str(x)).lower(), inplace=True)
fair_gdp.rename(columns={"region": "country_iso"}, inplace=True)
fair_gdp["year"] = pandas.to_numeric(fair_gdp["year"].str.replace("y", ""))

# Load GFPMX GDP data
# Expressed in 1000 USD of 2017
gfpm_gdp = gfpmx_data.get_sheet_long("gdp").merge(
    country_iso_codes, on="country", how="left"
)
# Convert from 1000 USD to million USD
gfpm_gdp["gdp"] = gfpm_gdp["gdp"] / 1e3
gfpm_gdp.rename(columns={"gdp": "gfpm_gdp"}, inplace=True)

# Load World bank GDP data in PPP constant USD of 2017
# https://data.worldbank.org/indicator/NY.GDP.MKTP.PP.KD
wb_gdp = world_bank.db.select("indicator", indicator_code="NY.GDP.MKTP.PP.KD")
wb_gdp.rename(columns={"reporter_code": "country_iso", "value": "wb_gdp"}, inplace=True)
# Convert from USD to million USD
wb_gdp["wb_gdp"] = wb_gdp["wb_gdp"] / 1e6


# Max GDP per region
bau_gdp.loc[bau_gdp.groupby("country_iso")["ssp2"].idxmax()]
bau_gdp.query("country_iso=='FRA'")

# Check that there are no NA values for EU country ISO codes
selector = gfpm_gdp["country"].isin(faostat.country_groups.eu_country_names)
assert not any(gfpm_gdp[selector]["country_iso"].isna())

# Merge GFPM, Magpie and world bank data and compare the GDP of EU countries in 2030
index = ["country_iso", "year"]
comp = (
    gfpm_gdp[index + ["country", "gfpm_gdp"]]
    .merge(bau_gdp[index + ["ssp2"]], on=index, how="left")
    .merge(wb_gdp[index + ["wb_gdp"]], on=index, how="left")
)
selector = comp["country"].isin(faostat.country_groups.eu_country_names)
compeu = comp[selector].copy()

# Reshape to long format
compeu_long = compeu.melt(
    id_vars=["country_iso", "year", "country"], var_name="source", value_name="gdp"
)

# Plot
# index = ["country_iso", "year", "country"]
# comp.set_index("year").plot(title="Compare MagPie do World Bank")
# plt.show()


#######################
# XY comparison plots #
#######################
compeu["country"] = compeu["country"].astype("category")
g = seaborn.FacetGrid(
    compeu.query("not ssp2.isna()"),
    col="country",
    col_wrap=6,
    sharex=False,
    sharey=False,
)  # , height=6)
g.map_dataframe(seaborn.scatterplot, x="gfpm_gdp", y="ssp2", hue="country")
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
compeu_long["gdp_b"] = compeu_long["gdp"] / 1e3
g = seaborn.relplot(
    data=compeu_long,
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


# Compute yearly increase by variable
