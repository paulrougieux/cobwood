""" This script is deprecated, see the xarray version.

Functions to implement equations in the paper

    Buongiorno, J. (2021). GFPMX: A Cobweb Model of the Global Forest Sector, with
    an Application to the Impact of the COVID-19 Pandemic. Sustainability, 13(10),
    5507.

    https://www.mdpi.com/2071-1050/13/10/5507

    Local link

    ~/repos//bioeconomy_papers/literature/buongiorno2021_gfpmx_a_cobweb_model_of_the_global_forest_sector_with_an_application_to_the_impact_of_the_covid_19_pandemic.pdf

Excel file "~/large_models/GFPMX-8-6-2021.xlsx"
"""

# Third party modules
import numpy


def shift_index(x):
    """Update the index of a lagged variable
    To store last year's prices in a "price_lag" column at year t.
    We first need to update the index from year t-1 to year t.
    Otherwise assignation of .loc[[t], "price_lag"] would contain NA values.

    :param x pandas series input variable indexed by year and country
    :return pandas series
    """
    df = x.reset_index()
    df["year"] = df["year"] + 1
    x_lag = df.set_index(x.index.names)[x.name]
    return x_lag


def compute_demand(df):
    """GFPMX demand equation 1"""
    return (
        df["cons_constant"]
        * df["price_lag"].pow(df["cons_price_elasticity"])
        * df["gdp"].pow(df["cons_gdp_elasticity"])
    )


def compute_import_demand(df):
    """GFPMX import demand equation 4"""
    return (
        df["imp_constant"]
        * (df["price_lag"] * (1 + df["tariff_lag"])).pow(df["imp_price_elasticity"])
        * df["gdp"].pow(df["imp_gdp_elasticity"])
    )


def compute_export_supply(df):
    """GFPMX export supply equation 7"""
    world_imp = df["imp"].sum()
    exp = df["exp_marginal_propensity_to_export"] * world_imp + df["exp_constant"]
    # Use numpy.maximum to propagate NA values
    return numpy.maximum(exp, 0)


def compute_domestic_production(df):
    """GFPMX domestic production equation 8

    Replace negative values by zero"""
    prod = df["cons"] + df["exp"] - df["imp"]
    prod.loc[prod < 0] = 0
    return prod


def compute_world_price(s_world, s_primary_world):
    """GFPMX world price as a function of the input price
    - World price of f, s, u, l as a function of the roundwood price equation 10
    - World price of paper as a function of the pulp price equation 11
    """
    return s_world["price_constant"] * pow(
        s_primary_world["price"], s_world["price_input_elast"]
    )


def compute_local_price(df, s_world):
    """GFPMX local price as a function of the world price equation 12"""
    # world_price = s_world.xs("WORLD", level="country")["price"].iat[0]
    price = df["price_constant"] * pow(
        s_world.loc["price2"], df["price_world_price_elasticity"]
    )
    return price
