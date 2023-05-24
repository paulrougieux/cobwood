#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A script to compute GFPMX sawnwood equations recursively in a time loop

Run this file with:

     ipython -i ~/repos/cobwood/scripts/compute_sawnwood_equations.py

Equation numbers in this script refer to the paper:

    Buongiorno, J. (2021). GFPMX: A Cobweb Model of the Global Forest Sector, with
    an Application to the Impact of the COVID-19 Pandemic. Sustainability, 13(10),
    5507.

    https://www.mdpi.com/2071-1050/13/10/5507

    Local link

    ~/repos//bioeconomy_papers/literature/buongiorno2021_gfpmx_a_cobweb_model_of_the_global_forest_sector_with_an_application_to_the_impact_of_the_covid_19_pandemic.pdf

Excel file "~/large_models/GFPMX-8-6-2021.xlsx"
"""

# Third party modules
from numpy.testing import assert_allclose

# Internal modules
from cobwood.gfpmx_data import gfpmx_data
from cobwood.gfpmx_functions import (
    shift_index,
    compute_demand,
    compute_import_demand,
    compute_export_supply,
    compute_domestic_production,
    compute_world_price,
    compute_local_price,
)

# Load sawnwood data
sawn = gfpmx_data.get_country_rows("sawn", ["gdp"])
sawn_agg = gfpmx_data.get_agg_rows("sawn", ["gdp"])
# Load industrial roundwood aggregates
indround_agg = gfpmx_data.get_agg_rows("indround")

# Check that world aggregates correspond to the sum of countries
gfpmx_data.check_world_aggregates("sawn", ["gdp"])


# Display the number of years and number of countries
years = sawn.index.to_frame()["year"].unique()
countries = sawn.index.to_frame()["country"].unique()
print("Years:", years)
print("Countries:", countries)
print("Number of lines in the sawn data frame:", len(sawn))
print(
    "Number of years time the number of countries: ",
    len(years),
    "*",
    len(countries),
    "=",
    len(years) * len(countries),
)

# Start one year after the base year so price_{t-1} exists already
for t in range(gfpmx_data.base_year + 1, years.max() + 1):
    # Keep `[t]` in square braquets so that years is kept in the index on both sides
    sawn.loc[[t], "price_lag"] = shift_index(sawn.loc[[t - 1], "price"])
    sawn.loc[[t], "tariff_lag"] = shift_index(sawn.loc[[t - 1], "tariff"])
    sawn.loc[[t], "cons2"] = compute_demand(sawn.loc[[t]])
    sawn.loc[[t], "imp2"] = compute_import_demand(sawn.loc[[t]])
    sawn.loc[[t], "exp2"] = compute_export_supply(sawn.loc[[t]])
    sawn.loc[[t], "prod2"] = compute_domestic_production(sawn.loc[[t]])
    sawn_agg.loc[(t, "WORLD"), "price2"] = compute_world_price(
        sawn_agg.loc[(t, "WORLD")], indround_agg.loc[(t, "WORLD")]
    )
    sawn.loc[[t], "price2"] = compute_local_price(
        sawn.loc[[t]], sawn_agg.loc[(t, "WORLD")]
    )


##################################
# Post processing quality checks #
##################################
# TODO use np.testing.assert_allclose()
# Check that the computed values correspond to the original GFPMx values
# Compare only values after the base year
sawn_comp = sawn.query("year > @gfpmx_data.base_year + 1")
for var in ["cons", "imp", "exp", "prod", "price"]:
    try:
        assert_allclose(sawn_comp[var + "2"], sawn_comp[var], rtol=1e-6)
    except AssertionError as e:
        print("The", var, "variable does not match with original GFPMx data:\n", str(e))


# sawn.to_csv("/tmp/sawn.csv") # Open with gx
