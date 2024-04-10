"""Load Eurostat population data

Load historical population data, load population projections, merge them together.

Sources:

    - Historical data
    https://ec.europa.eu/eurostat/web/population-demography/demography-population-stock-balance/database

    - Population projections
    https://ec.europa.eu/eurostat/web/population-demography/population-projections/database

Usage:

    >>> from cobwood.eurostat.population import load_hist_population_and_proj
    >>> popt = load_hist_population_and_proj("eurostat_tps00001_page.tsv", "eurostat_proj_23np.tsv")

Separate low level functions for information and debugging:

    >>> from cobwood.eurostat.population import load_eurostat
    >>> from cobwood.eurostat.population import combine_hist_population_to_proj
    >>> # Load Eurostat historical population
    >>> from cobwood.eurostat.population import load_hist_population_and_proj
    >>> pop_hist = load_eurostat("eurostat_tps00001_page.tsv")
    >>> # Load Eurostat population projection
    >>> pop_proj_23 = load_eurostat("eurostat_proj_23np.tsv")
    >>> # combine them in one data frame
    >>> popt = combine_hist_population_to_proj(pop_hist, pop_proj_23)
    >>> # Descriptive statistics of the projections
    >>> for col in ["freq", "projection", "sex", "age", "unit", "geo", "year"]:
    >>>     print(col, ":", pop_proj_23[col].unique())

Plot the historical population data and baseline projection

    >>> from matplotlib import pyplot as plt
    >>> popt.set_index("year").plot()
    >>> plt.show()

Plot all projections

    >>> selector = pop_proj_23["geo"] == "EU27_2020"
    >>> selector &= pop_proj_23["sex"] == "T"
    >>> pop_proj_23["value_m"] =  pop_proj_23["value"] / 1e6
    >>> proj_wide = pop_proj_23.loc[selector].pivot(columns="projection", index="year", values="value_m")
    >>> proj_wide.plot(title="EU population projection in million inhabitants")
    >>> plt.show()

"""

import pandas
from pandas.api.types import is_string_dtype
from cobwood import cobwood_data_dir


def reformat_eurostat(df):
    """Reformat the first columns of a eurostat tab separated value dataset
    which are actually comma separated values, reshape year in long format."""
    raw_first_col = df.columns[0]
    col_names = df.columns.str.replace("\\TIME_PERIOD", "")[0].split(",")
    df[col_names] = df[raw_first_col].str.split(",", expand=True)
    df.drop(columns=raw_first_col, inplace=True)
    # Clean column names
    df.columns = df.columns.str.replace(" ", "")
    # Reshape to long format
    df_long = df.melt(id_vars=col_names, var_name="year", value_name="value")
    df_long["year"] = df_long["year"].astype(int)
    # If value is a string column, separate the flag to a new column
    if is_string_dtype(df_long["value"]):
        df_long[["value", "flag"]] = df_long["value"].str.split(" ", n=1, expand=True)
    return df_long


def load_eurostat(file_name):
    """Load and reformat a Eurostat data frame"""
    df = pandas.read_table(cobwood_data_dir / "eurostat" / file_name)
    df = reformat_eurostat(df)
    return df


def combine_hist_population_to_proj(df_hist, df_proj):
    """Prepare population projection by interpolating missing years in the
    projection (which has a 5 years interval) and adding data for the
    historical period. df_hist contains the historical data, df_proj contains
    the projection data."""
    # Combine historical data and projection
    year_max_hist = int(df_hist["year"].max())
    # Keep only total EU population
    selector_proj = df_proj["geo"] == "EU27_2020"
    # BSL is the baseline projection
    selector_proj &= df_proj["projection"] == "BSL"
    selector_proj &= df_proj["sex"] == "T"
    selector_proj &= df_proj["year"] > year_max_hist
    selector_hist = df_hist["geo"] == "EU27_2020"
    cols = ["freq", "geo", "year", "value"]
    df = pandas.concat(
        [df_hist.loc[selector_hist, cols], df_proj.loc[selector_proj, cols]],
        ignore_index=True,
    )
    # The projection is on a 5 years interval.
    # Interpolate between missing years.
    more_years = pandas.DataFrame({"year": range(min(df["year"]), max(df["year"]))})
    df = df.merge(more_years, on="year", how="outer")
    df.sort_values("year", inplace=True)
    df["value"] = pandas.to_numeric(df["value"], errors="coerce")
    df["value"] = df["value"].interpolate(method="linear")
    df["freq"] = df["freq"].ffill()
    df["geo"] = df["geo"].ffill()
    return df


def load_hist_population_and_proj(file_hist, file_proj):
    """Load historical population and population projection total EU"""
    pop_hist = load_eurostat(file_hist)
    pop_proj = load_eurostat(file_proj)
    # combine them in one data frame
    df = combine_hist_population_to_proj(pop_hist, pop_proj)
    return df
