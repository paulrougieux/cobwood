"""This scripts computes all GFPMx equations using xarray

Usage:

    ipython -i ~/repos/cobwood/scripts/compute_all_equations_with_xarray.py

See also:

- A drawing illustrating the model structure in
  draft_articles/gftm_degrowth/model_structure.odg

- Buongiorno, J. (2021). GFPMX: A Cobweb Model of the Global Forest Sector,
  with an Application to the Impact of the COVID-19 Pandemic. Sustainability,
  13(10), 5507. https://www.mdpi.com/2071-1050/13/10/5507

Advantages of using xarray over pandas:

- The shift_index() function is not needed any more, we can call
  sawn["price"].loc[:, t - 1] directly.

TODO:

- Evaluate whether it is better to keep countries and aggregates in the same dataset.

  Option A If countries and aggregates are in the same dataset, consumption should be
  computed for countries only first, the aggregates computed later.

        ds["cons_constant"]
        * pow(ds["price"].loc[COUNTRIES, t - 1], ds["cons_price_elasticity"])
        * pow(ds["gdp"].loc[COUNTRIES, t], ds["cons_gdp_elasticity"])

  World price is

        ds["price_constant"].loc["WORLD"]
        * pow(ds_primary["price"].loc["WORLD", t], ds["price_input_elast"].loc["WORLD"])

  Should the .loc["WORLD"] and .loc[COUNTRIES] be done when the function is
  called? No better to leave no ambiguity.


  Option B If there was a dataset of countries only and a dataset of aggregates only we
  would compute consumption as such:

        ds["cons_constant"]
        * pow(ds["price"].loc[:, t - 1], ds["cons_price_elasticity"])
        * pow(ds["gdp"].loc[:, t], ds["cons_gdp_elasticity"])

  World prices would be computed as:

        ds_agg["price_constant"].loc["WORLD"]
        * pow(ds_primary_agg["price"].loc["WORLD", t], ds_agg["price_input_elast"].loc["WORLD"])

"""

import numpy as np
from numpy.testing import assert_allclose
import xarray

# import pandas
# import seaborn

from cobwood.gfpmx_data import gfpmx_data
from cobwood.gfpmx_data import convert_to_2d_array

# Reproduce bugs in GFPMX-8-6-2021.xlsx
GFPMX_8_6_2021_COMPATIBLE_MODE = True
# List of bugs:
# 1) Indonesia has negative industrial roundwood consumption because
#    =IF($PulpProd.AK118+$PanelProd.AK118+$SawnProd.AK118<=0,0,$G118*($IndroundPrice.AJ118^$D118)*($PulpProd.AK118+$PanelProd.AK118+$SawnProd.AK118)^$E118)
#    Is equal to -57. The if condition should be on the whole expression result,
#    but it's only the sum of the secondary products production.


# Load reference data
other_ref = gfpmx_data.convert_sheets_to_dataset("other")
indround_ref = gfpmx_data.convert_sheets_to_dataset("indround")
round_ref = gfpmx_data.convert_sheets_to_dataset("round")
fuel_ref = gfpmx_data.convert_sheets_to_dataset("fuel")
sawn_ref = gfpmx_data.convert_sheets_to_dataset("sawn")
panel_ref = gfpmx_data.convert_sheets_to_dataset("panel")
pulp_ref = gfpmx_data.convert_sheets_to_dataset("pulp")
paper_ref = gfpmx_data.convert_sheets_to_dataset("paper")
gdp = convert_to_2d_array(gfpmx_data.get_sheet_wide("gdp"))

COUNTRY_AGGREGATES = gfpmx_data.country_aggregates
COUNTRIES = sawn_ref.country[~sawn_ref.country.isin(COUNTRY_AGGREGATES)].values
# Check that all countries in the dataset are also present in the list
assert set(list(COUNTRIES)) - set(gfpmx_data.country_groups["country"]) == set()
# Check that all countries present in the list are also in the dataset
assert set(gfpmx_data.country_groups["country"]) - set(list(COUNTRIES)) == set()

######################################################
# Erase data after base year and copy the data frame #
######################################################
# Using a mask makes the dataset return an error on loc selection
# base_year = 2018
# mask = sawn.coords["year"] > base_year
# sawn = xarray.where(mask, np.nan, sawn_ref).copy()
# sawn["price"].loc[:,t-1]
# # returns KeyError: 2018
# # But selecting the original data works fine
# sawn_ref["price"].loc[:,t-1]
# --> Make a reproducible example and ask on Stackoverflow why this is the case.
# We will compute demand from the base_year + 1


def remove_after_base_year_and_copy(ds: xarray.Dataset, base_year):
    """Remove values after the base year and return a deep copy of the
    input dataset, i.e. the input dataset is not modified.
    This applies only to arrays which have a time dimension.
    Keep future tariff data, since they are exogenous.
    """
    ds_out = ds.copy(deep=True)
    for x in ds_out.data_vars:
        if len(ds_out[x].dims) == 2 and "tariff" not in x:
            ds_out[x].loc[dict(year=ds_out.coords["year"] > base_year)] = np.nan
    return ds_out


other = remove_after_base_year_and_copy(other_ref, 2018)
fuel = remove_after_base_year_and_copy(fuel_ref, 2018)
indround = remove_after_base_year_and_copy(indround_ref, 2018)
# Use an underscore so that we don't overwrite the python round() function
round_ = remove_after_base_year_and_copy(round_ref, 2018)
sawn = remove_after_base_year_and_copy(sawn_ref, 2018)
panel = remove_after_base_year_and_copy(panel_ref, 2018)
pulp = remove_after_base_year_and_copy(pulp_ref, 2018)
paper = remove_after_base_year_and_copy(paper_ref, 2018)

# Add GDP projections to the datasets gdp are projected to the future
sawn["gdp"] = gdp
round_["gdp"] = gdp
panel["gdp"] = gdp
fuel["gdp"] = gdp
paper["gdp"] = gdp


def consumption(ds: xarray.Dataset, t: int) -> xarray.DataArray:
    """Compute consumption equation 1"""
    return (
        ds["cons_constant"]
        * pow(ds["price"].loc[COUNTRIES, t - 1], ds["cons_price_elasticity"])
        * pow(ds["gdp"].loc[COUNTRIES, t], ds["cons_gdp_elasticity"])
    )


def consumption_pulp(
    ds: xarray.Dataset, ds_paper: xarray.Dataset, t: int
) -> xarray.DataArray:
    """Compute the Domestic Demand for Wood Pulp equation 2"""
    return (
        ds["cons_constant"]
        * pow(ds["price"].loc[COUNTRIES, t - 1], ds["cons_price_elasticity"])
        * pow(
            ds_paper["prod"].loc[COUNTRIES, t], ds["cons_paper_production_elasticity"]
        )
    )


def consumption_indround(
    ds: xarray.Dataset,
    ds_sawn: xarray.Dataset,
    ds_panel: xarray.Dataset,
    ds_pulp: xarray.Dataset,
    t: int,
    compatible_mode: bool = None,
) -> xarray.DataArray:
    """Domestic demand for industrial roundwood equation 3

    The argument `compatible_mode` is to reproduce a behaviour in GFPMX-8-6-2021.xlsx
    for comparison purposes. Content of cell AJ2 in sheet IndroundCons:
    =IF($PulpProd.AJ2+$PanelProd.AJ2+$SawnProd.AJ2<=0,0,
        $G2*($IndroundPrice.AI2^$D2)*($PulpProd.AJ2+$PanelProd.AJ2+$SawnProd.AJ2)^$E2)
    The if condition is only the sum of the 3 secondary products production.
    Because Singapore has a negative constant (column G), it results in a negative consumption.
    """
    if compatible_mode is None:
        compatible_mode = GFPMX_8_6_2021_COMPATIBLE_MODE
    sum_prod_secondary = (
        ds_sawn["prod"].loc[COUNTRIES, t]
        + ds_panel["prod"].loc[COUNTRIES, t]
        + ds_pulp["prod"].loc[COUNTRIES, t]
    )
    cons = (
        ds["cons_constant"].loc[COUNTRIES]
        * pow(
            ds["price"].loc[COUNTRIES, t - 1],
            ds["cons_price_elasticity"].loc[COUNTRIES],
        )
        * pow(
            sum_prod_secondary,
            ds["cons_products_elasticity"],
        )
    )
    if compatible_mode:
        # Keep only rows where sum_prod_secondary is positive
        cons.loc[sum_prod_secondary < 0] = 0
        return cons
    # Keep only rows where consumption is positive
    return np.maximum(cons, 0)


def import_demand(ds: xarray.Dataset, t: int) -> xarray.DataArray:
    """Compute import demand equation 4"""
    return (
        ds["imp_constant"]
        * pow(
            ds["price"].loc[COUNTRIES, t - 1] * (1 + ds["tariff"].loc[:, t - 1]),
            ds["imp_price_elasticity"],
        )
        * pow(ds["gdp"].loc[COUNTRIES, t], ds["imp_gdp_elasticity"])
    )


def import_demand_pulp(
    ds: xarray.Dataset, ds_paper: xarray.Dataset, t: int
) -> xarray.DataArray:
    """Compute the import demand for Wood Pulp equation 5"""
    # =$G2*(($PulpPrice.AI2*(1+$PulpTariff.AI2))^$D2)*($PaperProd.AJ2^$E2)
    return (
        ds["imp_constant"]
        * pow(
            ds["price"].loc[COUNTRIES, t - 1]
            * (1 + ds["tariff"].loc[COUNTRIES, t - 1]),
            ds["imp_price_elasticity"],
        )
        * pow(ds_paper["prod"].loc[COUNTRIES, t], ds["imp_paper_production_elasticity"])
    )


def import_demand_indround(
    ds: xarray.Dataset,
    ds_sawn: xarray.Dataset,
    ds_panel: xarray.Dataset,
    ds_pulp: xarray.Dataset,
    t: int,
    compatible_mode: bool = None,
) -> xarray.DataArray:
    """Compute the import demand of industrial roundwood equation 6"""
    if compatible_mode is None:
        compatible_mode = GFPMX_8_6_2021_COMPATIBLE_MODE
    sum_prod_secondary = (
        ds_sawn["prod"].loc[COUNTRIES, t]
        + ds_panel["prod"].loc[COUNTRIES, t]
        + ds_pulp["prod"].loc[COUNTRIES, t]
    )
    imp = (
        ds["imp_constant"].loc[COUNTRIES]
        * pow(
            (1 + ds["tariff"].loc[COUNTRIES, t]) * ds["price"].loc[COUNTRIES, t - 1],
            ds["imp_price_elasticity"].loc[COUNTRIES],
        )
        * pow(sum_prod_secondary, ds["imp_products_elasticity"].loc[COUNTRIES])
    )
    if compatible_mode:
        # Keep only rows where sum_prod_secondary is positive
        imp.loc[sum_prod_secondary < 0] = 0
        return imp
    # Keep only rows where import demand is positive
    return np.maximum(imp, 0)


def export_supply(ds: xarray.Dataset, t: int) -> xarray.DataArray:
    """Compute export supply equation 7

    Replace negative values by zero."""
    world_imp = ds["imp"].loc[COUNTRIES, t].sum()
    exp = (
        ds["exp_marginal_propensity_to_export"].loc[COUNTRIES] * world_imp
        + ds["exp_constant"]
    )
    return np.maximum(exp, 0)


def production(ds: xarray.Dataset, t: int) -> xarray.DataArray:
    """Compute domestic production equation 8
    Replace negative values by zero
    """
    prod = (
        ds["cons"].loc[COUNTRIES, t]
        + ds["exp"].loc[COUNTRIES, t]
        - ds["imp"].loc[COUNTRIES, t]
    )
    return np.maximum(prod, 0)


def world_price(
    ds: xarray.Dataset, ds_primary: xarray.Dataset, t: int
) -> xarray.DataArray:
    """Compute the world price equation 10
    as a function of the input price
    """
    return ds["price_constant"].loc["WORLD"] * pow(
        ds_primary["price"].loc["WORLD", t], ds["price_input_elast"].loc["WORLD"]
    )


def world_price_indround(
    ds: xarray.Dataset, ds_other: xarray.Dataset, t: int
) -> xarray.DataArray:
    """Compute the world price of industrial roundwood equation 9"""
    # =$G182*($IndroundProd.AJ182^$F182)*($Stock.AJ182^$E182)*EXP($D182*AJ1)
    return (
        ds["price_constant"].loc["WORLD"]
        * pow(
            ds["prod"].loc["WORLD", t],
            ds["price_world_price_elasticity"].loc["WORLD"],
        )
        * pow(
            ds_other["stock"].loc["WORLD", t],
            ds["price_stock_elast"].loc["WORLD"],
        )
        * np.exp(ds["price_trend"].loc["WORLD"] * t)
    )


def local_price(ds: xarray.Dataset, t: int) -> xarray.DataArray:
    """Compute the local price equation 12"""
    return ds["price_constant"].loc[COUNTRIES] * pow(
        ds["price"].loc["WORLD", t], ds["price_world_price_elasticity"].loc[COUNTRIES]
    )


def forest_stock(
    ds: xarray.Dataset, ds_round: xarray.Dataset, t: int
) -> xarray.DataArray:
    """Compute the forest stock expressed as growth drain equation 15

    Notes:
    - Roundwood is the sum of industrial round wood and fuel wood.
    - Replaces negative values by zero
    - Converts the stock from thousand m3 to million m3
        - TODO remove this conversion? Currently kept for comparison purposes with GFPMx.
            - Other units are in 1000 m3, should the whole model be harmonized to m3?
    """
    stock = (
        ds["stock"].loc[COUNTRIES, t - 1]
        * (1 + ds["stock_stock_growth_rate_without_harvest"].loc[COUNTRIES])
        - ds["stock_harvest_effect_on_stock"].loc[COUNTRIES]
        * ds_round["prod"].loc[COUNTRIES, t - 1]
        / 1000
    )
    return np.maximum(stock, 0)


def compute_country_aggregates(
    ds: xarray.Dataset, t: int, variable: str = None
) -> None:
    """Compute aggregates for 'WORLD' and for
    'AFRICA', 'NORTH AMERICA', 'SOUTH AMERICA', 'ASIA', 'OCEANIA', 'EUROPE'
    param: ds dataset
    param: t time in years
    param: variable list of variables to aggregate in the dataset
    ! This function modifies its input data set `ds` for the given time step t.
    """
    regions = [x for x in COUNTRY_AGGREGATES if x != "WORLD"]
    if variable is None:
        variable = ["cons", "exp", "imp", "prod"]
    if isinstance(variable, str):
        variable = [variable]
    for var in variable:
        ds[var].loc["WORLD", t] = ds[var].loc[COUNTRIES, t].sum()
        ds[var].loc[regions, t] = (
            ds[var].loc[COUNTRIES, t].groupby(ds["region"].loc[COUNTRIES]).sum()
        )


def compute_secondary_product_ciep(
    ds: xarray.Dataset, ds_primary: xarray.Dataset, t: int
) -> None:
    """Compute consumption, import, export and production equations
    corresponding to a semi finished (secondary) product.

    ! This function modifies the input data set `ds` for the given time step t.
    """
    ds["cons"].loc[COUNTRIES, t] = consumption(ds, t)
    ds["imp"].loc[COUNTRIES, t] = import_demand(ds, t)
    ds["exp"].loc[COUNTRIES, t] = export_supply(ds, t)
    ds["prod"].loc[COUNTRIES, t] = production(ds, t)


def compute_secondary_product_price(
    ds: xarray.Dataset, ds_primary: xarray.Dataset, t: int
) -> None:
    """Compute world prices and local prices
    ! This function modifies the input data set `ds` for the given time step t.
    """
    ds["price"].loc["WORLD", t] = world_price(ds, ds_primary, t)
    ds["price"].loc[COUNTRIES, t] = local_price(ds, t)


#########################
# Compute one time step #
#########################
year = 2019

# 1. Compute stock growth and drain from stock and production at t-1
other["stock"].loc[COUNTRIES, year] = forest_stock(other, round_, year)

# 2. Compute cons, imp, exp and prod of secondary products
compute_secondary_product_ciep(sawn, indround, year)
compute_secondary_product_ciep(fuel, indround, year)
compute_secondary_product_ciep(panel, indround, year)
compute_secondary_product_ciep(paper, pulp, year)

# 3. Compute cons, imp, exp and prod of primary products
pulp["cons"].loc[COUNTRIES, year] = consumption_pulp(pulp, paper, year)
pulp["imp"].loc[COUNTRIES, year] = import_demand_pulp(pulp, paper, year)
pulp["exp"].loc[COUNTRIES, year] = export_supply(pulp, year)
pulp["prod"].loc[COUNTRIES, year] = production(pulp, year)
indround["cons"].loc[COUNTRIES, year] = consumption_indround(
    indround, sawn, panel, pulp, year
)
indround["imp"].loc[COUNTRIES, year] = import_demand_indround(
    indround, sawn, panel, pulp, year
)
indround["exp"].loc[COUNTRIES, year] = export_supply(indround, year)
indround["prod"].loc[COUNTRIES, year] = production(indround, year)

# 4. Compute prices
compute_country_aggregates(indround, year)
compute_country_aggregates(other, year, "stock")
indround["price"].loc["WORLD", year] = world_price_indround(indround, other, year)
indround["price"].loc[COUNTRIES, year] = local_price(indround, year)
# The world price of indround is required to compute the price of secondary products
assert not indround["price"].loc["WORLD", year].isnull()
compute_secondary_product_price(sawn, indround, year)
compute_secondary_product_price(fuel, indround, year)
compute_secondary_product_price(panel, indround, year)
compute_secondary_product_price(pulp, indround, year)
# The world price of pulp is required to compute the price of paper
assert not pulp["price"].loc["WORLD", year].isnull()
compute_secondary_product_price(paper, pulp, year)


##########
# Checks #
##########
# Comparison between sawn modified in place by the
# compute_secondary_product_ciep() function
# and sawn2 computed below
sawn2 = sawn.copy(deep=True)
sawn2["cons"].loc[COUNTRIES, year] = consumption(sawn2, year)
sawn2["imp"].loc[COUNTRIES, year] = import_demand(sawn2, year)
sawn2["exp"].loc[COUNTRIES, year] = export_supply(sawn2, year)
sawn2["prod"].loc[COUNTRIES, year] = production(sawn2, year)
sawn2["price"].loc["WORLD", year] = world_price(sawn2, indround, year)
sawn2["price"].loc[COUNTRIES, year] = local_price(sawn2, year)
assert sawn.equals(sawn2)


# Compute roundwood as the sum of industrial round wood and fuel wood
round_["prod"].loc[COUNTRIES, year] = (
    indround["prod"].loc[COUNTRIES, year] + fuel["prod"].loc[COUNTRIES, year]
)


def compare_to_ref(
    ds: xarray.Dataset, ds_ref: xarray.Dataset, variable: [list, str], t: int
):
    """Compare the computed dataset to the reference dataset for the given t
    Example use:
        >>> compare_to_ref(sawn, sawn_ref, "price", 2019)
        >>> compare_to_ref(indround, indround_ref, ["cons", "imp"], 2019)
    """
    if isinstance(variable, str):
        variable = [variable]
    print(f"Checking {ds.product} {', '.join(variable)}")
    for var in variable:
        rtol = 1e-7
        if var == "prod":
            rtol = 1e-2
        try:
            assert_allclose(
                ds[var].loc[COUNTRIES, t],
                ds_ref[var].loc[COUNTRIES, t],
                rtol=rtol,
            )
        except AssertionError as e:
            first_line_of_error = "".join(str(e).split("\n")[:3])
            msg = f"{ds.product}, {var}, {t}: {first_line_of_error}"
            raise AssertionError(msg) from e
    print("    OK")


ciepp_vars = ["cons", "imp", "exp", "prod", "price"]
compare_to_ref(sawn, sawn_ref, ciepp_vars, 2019)
compare_to_ref(panel, panel_ref, ciepp_vars, 2019)
compare_to_ref(paper, paper_ref, ciepp_vars, 2019)
compare_to_ref(pulp, pulp_ref, ciepp_vars, 2019)
compare_to_ref(indround, indround_ref, ciepp_vars, 2019)

# Compare world price
assert_allclose(sawn["price"].loc["WORLD", year], sawn_ref["price"].loc["WORLD", year])

# Comparison in case of mismatch
sawn_df = sawn.loc[dict(country=COUNTRIES, year=year)].to_pandas().reset_index()
sawn_ref_df = sawn_ref.loc[dict(country=COUNTRIES, year=year)].to_pandas().reset_index()
cols_to_check = ["cons", "imp", "exp", "prod"]
print(sawn_df[cols_to_check])
print(sawn_ref_df[cols_to_check])
sawn_df["prod_diff"] = sawn_df["prod"] / sawn_ref_df["prod"] - 1
sawn_df["cons_diff"] = sawn_df["cons"] / sawn_ref_df["cons"] - 1
print(sawn_df[["cons_diff", "prod_diff"]].describe())
sawn_df[["country"] + cols_to_check + ["prod_diff"]].sort_values(
    "prod_diff", ascending=False
)
print(sawn_ref_df[["country"] + cols_to_check])


# Plot comparison
# sawn_df["reference"] = "no"
# sawn_ref_df["reference"] = "yes"
# sawn_comp = pandas.concat([sawn_df, sawn_ref_df])
# p = seaborn.scatterplot(x="country", y="prod", hue="reference", data=sawn_comp)
# plt.xticks(rotation=90)
# plt.show()
