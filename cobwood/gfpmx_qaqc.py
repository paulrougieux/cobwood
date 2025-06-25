"""The purpose of this script is to check data consistency.

For example the sum of country values should be equal to the world value.
"""
# TODO: compute world export/imports
# TODO: compute world production/consumption

import pandas
from numpy.testing import assert_allclose


def check_world_aggregates(df, df_agg, rtol=None):
    """Check that the world aggregate correspond to the sum of constituents
    Compare only columns where the sum makes sense

    :param df data frame: country data
    :param df_agg data frame: world and continent data
    :param rtol float: relative tolerance
    """
    if rtol is None:
        rtol = 1e-7
    # TODO: check that the continent aggregates match with
    # the sum of their constituents.
    cols_compare = [
        "cons",
        "cons_usd",
        "exp",
        "exp_usd",
        "imp",
        "imp_usd",
        "prod",
        "prod_usd",
        "gdp",
    ]
    idx = pandas.IndexSlice
    # TODO: keep only columns that are present
    # cols_compare = df[set(cols_compare) & set(df.columns)]
    world_sum_1 = df_agg.loc[idx[:, "WORLD"], cols_compare]
    world_sum_2 = df.groupby(["year"]).agg("sum")[cols_compare]
    assert_allclose(world_sum_1, world_sum_2, rtol=rtol)


def check_nrows_years_countries(df, dataset_name):
    """Check that the number of rows is equal to the number of years times the
    number of countries. Return a diagnostic message that can be printed
    """
    years = df.index.to_frame()["year"].unique()
    countries = df.index.to_frame()["country"].unique()
    assert len(years) * len(countries) == len(df)
    msg = "Number of years times the number of countries"
    msg += f" in the {dataset_name} data frame: "
    msg += f"{len(years)} * {len(countries)} = {len(years) * len(countries)}"
    return msg


##################################
# Post processing quality checks #
##################################
# TODO use np.testing.assert_allclose()
# Check that the computed values correspond to the original GFPMx values
# Compare only values after the base year


def compare_to_original_cobwood(df, variables=None, base_year=None):
    """Compare computed variables to the original GFTMx values
    After times t = base_year + 1
    """
    if variables is None:
        variables = ["cons", "imp", "exp", "prod", "price"]
    df_comp = df.query("year > @base_year + 1")
    for var in variables:
        try:
            assert_allclose(df_comp[var + "2"], df_comp[var], rtol=1e-6)
        except AssertionError as e:
            print(
                "The",
                var,
                "variable does not match with original GFPMx data:\n",
                str(e),
            )
