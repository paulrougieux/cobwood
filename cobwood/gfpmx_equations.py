"""Reimplement the GFPMx model with Xarray

Usage:

    >>> from cobwood.gfpmx_equations import compute_one_time_step

"""

import numpy as np
import xarray
import pandas

# Reproduce behaviour/bugs in GFPMX-8-6-2021.xlsx
GFPMX_8_6_2021_COMPATIBLE_MODE = True
# List of bugs:
# 1) Indonesia has negative industrial roundwood consumption because
#    =IF($PulpProd.AK118+$PanelProd.AK118+$SawnProd.AK118<=0,0,$G118*($IndroundPrice.AJ118^$D118)*($PulpProd.AK118+$PanelProd.AK118+$SawnProd.AK118)^$E118)
#    Is equal to -57. The if condition should be on the whole expression result,
#    but it's only the sum of the secondary products production.


def consumption(ds: xarray.Dataset, t: int) -> xarray.DataArray:
    """Compute consumption equation 1"""
    return (
        ds["cons_constant"]
        * pow(ds["price"].loc[ds.c, t - 1], ds["cons_price_elasticity"])
        * pow(ds["gdp"].loc[ds.c, t], ds["cons_gdp_elasticity"])
    )


def consumption_pulp(
    ds: xarray.Dataset, ds_paper: xarray.Dataset, t: int
) -> xarray.DataArray:
    """Compute the Domestic Demand for Wood Pulp equation 2"""
    return (
        ds["cons_constant"]
        * pow(ds["price"].loc[ds.c, t - 1], ds["cons_price_elasticity"])
        * pow(
            ds_paper["prod"].loc[ds_paper.c, t], ds["cons_paper_production_elasticity"]
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
        ds_sawn["prod"].loc[ds_sawn.c, t]
        + ds_panel["prod"].loc[ds_panel.c, t]
        + ds_pulp["prod"].loc[ds_pulp.c, t]
    )
    cons = (
        ds["cons_constant"].loc[ds.c]
        * pow(
            ds["price"].loc[ds.c, t - 1],
            ds["cons_price_elasticity"].loc[ds.c],
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
            ds["price"].loc[ds.c, t - 1] * (1 + ds["tariff"].loc[:, t - 1]),
            ds["imp_price_elasticity"],
        )
        * pow(ds["gdp"].loc[ds.c, t], ds["imp_gdp_elasticity"])
    )


def import_demand_pulp(
    ds: xarray.Dataset, ds_paper: xarray.Dataset, t: int
) -> xarray.DataArray:
    """Compute the import demand for Wood Pulp equation 5"""
    # =$G2*(($PulpPrice.AI2*(1+$PulpTariff.AI2))^$D2)*($PaperProd.AJ2^$E2)
    return (
        ds["imp_constant"]
        * pow(
            ds["price"].loc[ds.c, t - 1] * (1 + ds["tariff"].loc[ds.c, t - 1]),
            ds["imp_price_elasticity"],
        )
        * pow(ds_paper["prod"].loc[ds.c, t], ds["imp_paper_production_elasticity"])
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
        ds_sawn["prod"].loc[ds_sawn.c, t]
        + ds_panel["prod"].loc[ds_panel.c, t]
        + ds_pulp["prod"].loc[ds_pulp.c, t]
    )
    imp = (
        ds["imp_constant"].loc[ds.c]
        * pow(
            (1 + ds["tariff"].loc[ds.c, t]) * ds["price"].loc[ds.c, t - 1],
            ds["imp_price_elasticity"].loc[ds.c],
        )
        * pow(sum_prod_secondary, ds["imp_products_elasticity"].loc[ds.c])
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
    world_imp = ds["imp"].loc[ds.c, t].sum()
    exp = (
        ds["exp_marginal_propensity_to_export"].loc[ds.c] * world_imp
        + ds["exp_constant"]
    )
    return np.maximum(exp, 0)


def production(ds: xarray.Dataset, t: int) -> xarray.DataArray:
    """Compute domestic production equation 8
    Replace negative values by zero
    """
    prod = ds["cons"].loc[ds.c, t] + ds["exp"].loc[ds.c, t] - ds["imp"].loc[ds.c, t]
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
    return ds["price_constant"].loc[ds.c] * pow(
        ds["price"].loc["WORLD", t], ds["price_world_price_elasticity"].loc[ds.c]
    )


def forest_stock(
    ds: xarray.Dataset, ds_indround: xarray.Dataset, ds_fuel: xarray.Dataset, t: int
) -> xarray.DataArray:
    """Compute the forest stock expressed as growth drain equation 15

    Notes:
    - Roundwood is the sum of industrial round wood and fuel wood.
    - Replaces negative values by zero
    - Converts the stock from thousand m3 to million m3
        - TODO remove this conversion? Currently kept for comparison purposes with GFPMx.
            - Other units are in 1000 m3, should the whole model be harmonized to m3?
    """
    indround_fuel_prod = (
        ds_indround["prod"].loc[ds_indround.c, t - 1]
        + ds_fuel["prod"].loc[ds_fuel.c, t - 1]
    )
    stock = (
        ds["stock"].loc[ds.c, t - 1]
        * (1 + ds["stock_growth_rate_without_harvest"].loc[ds.c])
        - ds["stock_harvest_effect_on_stock"].loc[ds.c] * indround_fuel_prod / 1000
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
    regions = ds.region.to_series().unique()
    regions = [
        x for x in regions if x != "WORLD" and not pandas.isna(x) and not "" == x
    ]
    if variable is None:
        variable = ["cons", "exp", "imp", "prod"]
    if isinstance(variable, str):
        variable = [variable]
    for var in variable:
        if any(ds[var].loc[ds.c, t].isnull()):
            msg = f"NA values in {ds.product} {var}:\n"
            msg += f"{ds[var].loc[ds.c, t]}"
            raise ValueError(msg)
        ds[var].loc["WORLD", t] = ds[var].loc[ds.c, t].sum()
        ds[var].loc[regions, t] = (
            ds[var].loc[ds.c, t].groupby(ds["region"].loc[ds.c]).sum()
        )


def compute_secondary_product_ciep(
    ds: xarray.Dataset, ds_primary: xarray.Dataset, t: int
) -> None:
    """Compute consumption, import, export and production equations
    corresponding to a semi finished (secondary) product.

    ! This function modifies the input data set `ds` for the given time step t.
    """
    ds["cons"].loc[ds.c, t] = consumption(ds, t)
    ds["imp"].loc[ds.c, t] = import_demand(ds, t)
    ds["exp"].loc[ds.c, t] = export_supply(ds, t)
    ds["prod"].loc[ds.c, t] = production(ds, t)


def compute_secondary_product_price(
    ds: xarray.Dataset, ds_primary: xarray.Dataset, t: int
) -> None:
    """Compute world prices and local prices
    ! This function modifies the input data set `ds` for the given time step t.
    """
    ds["price"].loc["WORLD", t] = world_price(ds, ds_primary, t)
    ds["price"].loc[ds.c, t] = local_price(ds, t)


def compute_one_time_step(
    ds_indround, ds_fuel, ds_pulp, ds_sawn, ds_panel, ds_paper, ds_other, year
):
    """Modifies the input data sets in place
    TODO: change this to use the gfpmx_data as the unique argument
    This requires adding the boolean country indicator ds.c as a prerequisite"""
    # 1. Compute stock growth and drain from stock and production at t-1
    ds_other["stock"].loc[ds_other.c, year] = forest_stock(
        ds_other, ds_indround, ds_fuel, year
    )
    # 2. Compute cons, imp, exp and prod of secondary products
    compute_secondary_product_ciep(ds_sawn, ds_indround, year)
    compute_secondary_product_ciep(ds_fuel, ds_indround, year)
    compute_secondary_product_ciep(ds_panel, ds_indround, year)
    compute_secondary_product_ciep(ds_paper, ds_pulp, year)
    # 3. Compute cons, imp, exp and prod of primary products
    ds_pulp["cons"].loc[ds_pulp.c, year] = consumption_pulp(ds_pulp, ds_paper, year)
    ds_pulp["imp"].loc[ds_pulp.c, year] = import_demand_pulp(ds_pulp, ds_paper, year)
    ds_pulp["exp"].loc[ds_pulp.c, year] = export_supply(ds_pulp, year)
    ds_pulp["prod"].loc[ds_pulp.c, year] = production(ds_pulp, year)
    ds_indround["cons"].loc[ds_pulp.c, year] = consumption_indround(
        ds_indround, ds_sawn, ds_panel, ds_pulp, year
    )
    ds_indround["imp"].loc[ds_indround.c, year] = import_demand_indround(
        ds_indround, ds_sawn, ds_panel, ds_pulp, year
    )
    ds_indround["exp"].loc[ds_indround.c, year] = export_supply(ds_indround, year)
    ds_indround["prod"].loc[ds_indround.c, year] = production(ds_indround, year)
    # 4. Compute Country aggregates and prices
    compute_country_aggregates(ds_sawn, year)
    compute_country_aggregates(ds_panel, year)
    compute_country_aggregates(ds_pulp, year)
    compute_country_aggregates(ds_paper, year)
    compute_country_aggregates(ds_fuel, year)
    compute_country_aggregates(ds_indround, year)
    compute_country_aggregates(ds_other, year, "stock")
    # Compute the world price and the local price of indround
    ds_indround["price"].loc["WORLD", year] = world_price_indround(
        ds_indround, ds_other, year
    )
    ds_indround["price"].loc[ds_indround.c, year] = local_price(ds_indround, year)
    # The world price of indround is required to compute the price of secondary products
    assert not ds_indround["price"].loc["WORLD", year].isnull()
    compute_secondary_product_price(ds_sawn, ds_indround, year)
    compute_secondary_product_price(ds_fuel, ds_indround, year)
    compute_secondary_product_price(ds_panel, ds_indround, year)
    compute_secondary_product_price(ds_pulp, ds_indround, year)
    # The world price of ds_pulp is required to compute the price of ds_paper
    assert not ds_pulp["price"].loc["WORLD", year].isnull()
    compute_secondary_product_price(ds_paper, ds_pulp, year)
