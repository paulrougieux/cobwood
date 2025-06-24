#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Give access to the dataset from the GFPMX model by Joseph Buongiorno.
Originally released at
    https://buongiorno.russell.wisc.edu/gfpm/

Before using this object, the Excel file needs to be exported to csv files with:

    >>> from cobwood.gfpmx_spreadsheet_to_csv import gfpmx_spreadsheet_to_csv
    >>> gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-8-6-2021.xlsx")
    >>> gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-base2020.xlsx")
    >>> gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-base2021.xlsb")

The data will then be available in a sub directory of `cobweb.input_dir` with
the same name as the spreadsheet file (except that it will be in snake case
`gfpmx_8_6_2021`).

# TODO: update examples to use GFPMX.input_data instead of using this directly

    >>> from cobwood.gfpmx_data import GFPMXData
    >>> gfpmx_data_b2018 = GFPMXData(input_dir="gfpmx_8_6_2021")
    >>> gfpmx_data_b2020 = GFPMXData(input_dir="gfpmx_base2020")
    >>> gfpmx_data_b2021 = GFPMXData(input_dir="gfpmx_base2021")

You can view spreadsheets contents (loaded from intermediate csv files) by
selecting their names:

    >>> gfpmx_data_b2018.sheets
    >>> gfpmx_data_b2018["indroundprod"]
    >>> gfpmx_data_b2018["stock"]

You can load Xarray datasets with the `convert_sheets_to_dataset()` method.

    >>> indround = gfpmx_data_b2018.convert_sheets_to_dataset("indround")
    >>> sawn = gfpmx_data_b2018.convert_sheets_to_dataset("sawn")
    >>> other = gfpmx_data_b2018.convert_sheets_to_dataset("other")

"""

# Built in modules
import re

# Third party modules
import numpy as np
import pandas
import xarray
from numpy.testing import assert_allclose


def convert_to_2d_array(df: pandas.DataFrame) -> xarray.DataArray:
    """Convert the year columns of a data frame to a two dimensional data array
    In wide format the values are in one column for each year.

    Example use:

        >>> from cobwood.gfpmx_data import GFPMXData
        >>> from cobwood.gfpmx_data import convert_to_2d_array
        >>> gfpmx_data = GFPMXData(input_dir="gfpmx_8_6_2021")
        >>> sawnprice_df = gfpmx_data.get_sheet_wide("sawnprice")
        >>> sawnprice_da = convert_to_2d_array(sawnprice_df)
        >>> gdp_df = gfpmx_data.get_sheet_wide("gdp")
        >>> gdp_da = convert_to_2d_array(gdp_df)

    """
    cols = df.columns
    value_cols = cols[df.columns.str.contains("value")]
    da = xarray.DataArray(df.set_index("country")[value_cols], dims=["country", "year"])
    # Change year to an integer
    da["year"] = da["year"].str.replace("value_", "").astype(int)
    if "unit" in df.columns:
        # Store the unit as an attribute
        da.attrs["unit"] = df["unit"].unique()[0]
    return da


def convert_to_1d_array(df: pandas.DataFrame, var: str) -> xarray.DataArray:
    """Convert one column of a data frame to a one dimensional data array

    Example use:

        >>> from cobwood.gfpmx_data import GFPMXData
        >>> from cobwood.gfpmx_data import convert_to_1d_array
        >>> gfpmx_data = GFPMXData(input_dir="gfpmx_8_6_2021")
        >>> sawnprice_df = gfpmx_data.get_sheet_wide("sawnprice")
        >>> sawnprice_elast_da = convert_to_1d_array(sawnprice_df, "world_price_elasticity")

    """
    return xarray.DataArray(df.set_index("country")[var], dims=["country"])


def check_variable_presence(ds: xarray.Dataset) -> None:
    """Check that the required variables and coefficients are present to
    compute equations. Since various products have different equations, the
    requirements differ among primary and secondary products.
    """
    common_vars = [
        "cons",
        "cons_constant",
        "cons_price_elasticity",
        "cons_usd",
        "exp",
        "exp_usd",
        "exp_constant",
        "exp_marginal_propensity_to_export",
        "imp",
        "imp_constant",
        "imp_price_elasticity",
        "imp_usd",
        "nettrade",
        "nettrade_usd",
        "price",
        "price_constant",
        "price_world_price_elasticity",
        "prod",
        "prod_usd",
        "tariff",
    ]
    indround_vars = [
        "cons_products_elasticity",
        "imp_products_elasticity",
        "price_stock_elast",
    ]
    end_product_vars = [
        "cons_gdp_elasticity",
        "conspercap",
        "imp_gdp_elasticity",
        "price_input_elast",
    ]
    other_vars = [
        "area",
        "area_constant",
        "gdp",
        "gdppercap",
        "harvestperha",
        "harvestperstock",
        "population",
        "stock",
        "stock_harvest_effect_on_stock",
        "stock_growth_rate_without_harvest",
        "stockpercap",
        "stockperha",
        "totalcons_usd",
        "totalexp_usd",
        "totalimp_usd",
        "totalnettrade_usd",
        "totalprod_usd",
        "valueadded",
    ]
    # TODO: add checks for fuel wood
    data_vars = list(ds.data_vars)
    required_vars = set()
    if ds.attrs["product"] == "pulp":
        required_vars = common_vars
    if ds.attrs["product"] == "indround":
        required_vars = common_vars + indround_vars
    if ds.attrs["product"] in ["sawn", "panel", "paper"]:
        required_vars = common_vars + end_product_vars
    if ds.attrs["product"] == "other":
        required_vars = other_vars
    # Check that the required variables are present
    if not set(required_vars).issubset(data_vars):
        msg = "The following variables are missing from "
        msg += f"{ds.attrs['product']}:\n"
        msg += f"{set(required_vars) - set(data_vars)}"
        raise ValueError(msg)


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


def compare_to_ref(
    ds: xarray.Dataset,
    ds_ref: xarray.Dataset,
    variable: [list, str],
    t: int,
    rtol: int = None,
    strict: bool = True,
):
    """Compare the computed dataset to the reference dataset for the given t
    Example use:
        >>> compare_to_ref(sawn, sawn_ref, "price", 2019)
        >>> compare_to_ref(indround, indround_ref, ["cons", "imp"], 2019)
    """
    if rtol is None:
        rtol = 1e-6
    if isinstance(variable, str):
        variable = [variable]
    final_message = "."
    for var in variable:
        # Production requires a different tolerance for some reason
        if var == "prod":
            rtol = 1e-2
        try:
            assert_allclose(
                ds[var].loc[ds.c, t],
                ds_ref[var].loc[ds.c, t],
                rtol=rtol,
            )
        except AssertionError as e:
            first_line_of_error = "".join(str(e).split("\n")[:3])
            msg = f"{ds.product}, {var}, {t}: {first_line_of_error}"
            if strict:
                raise AssertionError(msg) from e
            else:
                final_message = "There were errors."
                print(e, msg)
    print(f"Check {ds.product} {', '.join(variable)}: {final_message}")


class GFPMXData:
    """
    Read data from the GFTMX data set.

    The GFTMX dataset was converted to csv files one for each sheet in the
    original Excel Spreadsheet. This singleton gives access to each file.

    Load sawnwood consumption data in long format:

    :param input_dir Location of the csv files
    :param base_year Simulation base year i.e. last year of historical data
           available in the spreadsheet

        >>> from cobwood.gfpmx_data import GFPMXData
        >>> gfpmx_data = GFPMXData(input_dir="gfpmx_8_6_2021")
        >>> swd_cons = gfpmx_data['sawncons']
        >>> swd_cons

    The GFPMX dataset is useful to:

        1. Verify the reproducibility of results given in the spreadsheet

        2. Reuse elasticities, tariffs, constants and other coefficients that cannot be
           estimated easily

    See also the script that moves data from the original Excel spreadsheet to CSV files:
    `scripts/gfpmx_spreadsheet_to_csv.py`
    """

    def __getitem__(self, sheet_name):
        """Return a data frame based on the GFPMX sheet name."""
        return self.get_sheet_long(sheet_name)

    def __init__(self, parent):
        self.parent = parent
        self.input_dir = self.parent.input_dir
        if not self.input_dir.exists():
            msg = "The input data directory specified in the scenario yaml file "
            msg += "doesn't exist.\n"
            msg += f"Input data directory: {self.input_dir}\n"
            msg += "Configuration file:"
            msg += f"{self.parent.scenario_yaml_path}\n"
            msg += f"{self.parent.config}\n"
            raise FileNotFoundError(msg)
        self.sheets = self.list_sheets()
        self.index_merge = ["year", "country", "faostat_name"]
        self.index = ["year", "country"]
        self.country_groups = self.get_country_groups()
        self.country_aggregates = [
            "WORLD",
            "AFRICA",
            "NORTH AMERICA",
            "SOUTH AMERICA",
            "ASIA",
            "OCEANIA",
            "EUROPE",
        ]
        assert set(self.country_aggregates) - set(self.country_groups["region"]) == {
            "WORLD"
        }

    def list_sheets(self):
        """List sheets available in the GFPMX data folder

        :return data frame with the sheet name, product and element

        For example show all sheets available

            >>> from cobwood.gfpmx_data import GFPMXData
            >>> from pandas.errors import EmptyDataError
            # TODO: update examples to use GFPMX.input_data
            >>> gfpmx_data = GFPMXData(input_dir="gfpmx_8_6_2021")
            >>> sheets = gfpmx_data.list_sheets()
            >>> sheets

        As a prerequisite to merge sheets together, the following code
        shows additional variables besides the value in each sheet:

            >>> known_columns = ['year', 'element', 'unit', 'country',
            >>>                  'faostat_name', 'value']
            >>> for prod in sheets["product"].unique():
            >>>     sheets_selected = sheets.query("product==@prod")
            >>>     print(f"Additional variables in '{prod}' related sheets:")
            >>>     for s in sheets_selected.index:
            >>>         try:
            >>>             df = gfpmx_data[s]
            >>>             columns = df.columns
            >>>         except EmptyDataError:
            >>>             print(f"   No data in the '{s}' file.")
            >>>             columns = ["no data"]
            >>>         print("  ", s, set(columns) - set(known_columns))

        List all columns in the roundwood related sheets

            >>> for name in sheets.query("product == 'round'").index:
            >>>     print(name, "\n",  gfpmx_data[name].columns.tolist())

        List all columns in the other sheets

            >>> for name in sheets.query("product == 'other'").index:
            >>>     if name in ["author", "names", "notes", "worldprice"]:
            >>>          continue
            >>>     print(name, "\n",  gfpmx_data[name].columns.tolist())

        Display the shape of the other sheets

            >>> for s in sheets.query("product == 'other'").index:
            >>>     try:
            >>>         print(s, gfpmx_data[s].shape)
            >>>     except EmptyDataError:
            >>>         print(f"No data in the '{s}' file.")
            >>>     except ValueError as e:
            >>>         print(f"Error in {s}: {e}")

        Display the faostat_name of the sawnwood sheets

            >>> for name in sheets.query("product == 'sawn'").index:
            >>>     print(name, "\n",  gfpmx_data[name]["faostat_name"].unique())

        """
        sheet_paths = self.input_dir.glob("**/*.csv")
        df = pandas.DataFrame({"file_name": [x.name for x in sheet_paths]})
        df["name"] = df.file_name.str.extract("(.*).csv")
        # Place product patterns in a capture group for extraction
        product_pattern = "fuel|indround|panel|paper|pulp|round|sawn"
        # Create a product column and an element column
        df[["product", "element"]] = df.name.str.extract(f"({product_pattern})?(.*)")
        df = df.sort_values(by=["product", "element"])
        df["product"] = df["product"].fillna("other")
        df = df[["name", "product", "element"]]
        df.set_index("name", inplace=True)
        return df

    def get_sheet_wide(self, sheet_name):
        """Read a csv file into a pandas data frame

        Example use

            >>> from cobwood.gfpmx_data import GFPMXData
            >>> gfpmx_data = GFPMXData(input_dir="gfpmx_8_6_2021")
            >>> print(gfpmx_data.get_sheet_wide("sawnprice"))

        """
        csv_file_name = self.input_dir / (sheet_name + ".csv")
        df = pandas.read_csv(csv_file_name)
        return df

    def get_sheet_long(self, sheet_name):
        """Read a csv file into a pandas data frame and reshape it to long format

        Example use

            >>> from cobwood.gfpmx_data import GFPMXData
            >>> gfpmx_data = GFPMXData(input_dir="gfpmx_8_6_2021")
            >>> print(gfpmx_data.get_sheet_long("sawncons"))

        """
        df_wide = self.get_sheet_wide(sheet_name=sheet_name)
        # Remove the underscore otherwise pandas.wide_to_long doesn't work
        df_wide.rename(
            columns=lambda x: re.sub(r"value_", "value", str(x)), inplace=True
        )
        # Reshape year columns to long format
        index = [x for x in df_wide.columns if not re.search("value", x)]
        df = pandas.wide_to_long(df_wide, stubnames="value", i=index, j="year")
        df.reset_index(inplace=True)
        # Rename the value column according to the shorter element part of the
        # file name. Note there is also an element column which we don't use
        # here.
        element = self.sheets.loc[sheet_name, "element"]
        df.rename(columns={"value": element}, inplace=True)

        # Prefix any columns that are not part of the index,
        # with the short element name
        index = ["faostat_name", "element", "unit", "country", "year", element]
        other_cols = list(set(df.columns) - set(index))
        other_cols_renamed = [element + "_" + x for x in other_cols]
        mapping = dict(zip(other_cols, other_cols_renamed))
        df.rename(columns=mapping, inplace=True)

        # Check that years are complete
        years = df["year"].unique()
        if not years.min() + len(years) - 1 == years.max():
            msg = f"The time series of '{sheet_name}' is not complete. "
            msg += "The following years are missing:\n"
            msg += str(set(range(years.min(), years.max() + 1)) - set(years))
            raise ValueError(msg)

        return df

    def get_gdp(self, sheet_name="gdp", index=None, var_name="gdp"):
        """Return a data frame of cleaned GDP values

        >>> from cobwood.gfpmx_data import GFPMXData
        >>> gfpmx_data = GFPMXData(input_dir="gfpmx_8_6_2021")
        >>> gfpmx_data.get_price_lag('sawnprice')

        """
        if index is None:
            index = ["id", "year", "country"]
        df = self.get_sheet_long(sheet_name)
        df = df[index + ["value"]]
        df.rename(columns={"value": var_name}, inplace=True)
        return df

    def get_price_lag(self, sheet_name, index=None, var_name="price"):
        """Return a price table with prices shifted by a one year lag

        >>> from cobwood.gfpmx_data import GFPMXData
        >>> gfpmx_data = GFPMXData(input_dir="gfpmx_8_6_2021")
        >>> gfpmx_data.get_price_lag('sawnprice')

        """
        if index is None:
            index = ["id", "year", "country"]
        df = self.get_sheet_long(sheet_name)
        df = df[index + ["value"]]
        df.rename(columns={"value": var_name}, inplace=True)
        # Shift prices by a one year lag
        df.set_index("year", inplace=True)
        df[var_name + "_lag"] = df.groupby(["id", "country"])[var_name].shift()
        df.reset_index(inplace=True)
        return df

    def join_sheets(self, product, other_element=None):
        """
        Merge all related data frames for a given product

        :param str product: selected product
        :param list other_element: list of element to be added from the
        rows where product is equal to "other"
        :return data frame

        For example join all roundwood sheets in one data frame and add a
        stock column.

            >>> from cobwood.gfpmx_data import GFPMXData
            >>> gfpmx_data = GFPMXData(input_dir="gfpmx_8_6_2021")
            >>> rwd = gfpmx_data.join_sheets("round", ["stock"])
            >>> rwd.columns

        Join sheets for all available products

            >>> for product in gfpmx_data.sheets["product"].unique():
            >>>     if product == "other":
            >>>         continue
            >>>     print(product)
            >>>     print(gfpmx_data.join_sheets(product).head())

        Join all other sheets

            >>> sheets = gfpmx_data.list_sheets()
            >>> other_sheets = sheets.query("product == 'other'")
            >>> other_element = other_sheets["element"].to_list()
            >>> for element in ["author", "names", "notes", "worldprice"]:
            >>>     other_element.remove(element)
            >>> other = gfpmx_data.join_sheets("round", other_element)
            >>> print(other.columns)
            >>> other[other.columns[other.columns.str.contains("unnamed")]]

        """

        # Join the product sheets together
        sheets = self.sheets[self.sheets["product"] == product]
        first_sheet = sheets.index[0]
        df_all = self.get_sheet_long(first_sheet)
        for name in sheets.index[1:]:
            df = self.get_sheet_long(name)
            # Keep only index columns or columns starting with element
            element = sheets.loc[name]["element"]
            cols = df.columns[df.columns.str.match("^" + element)].tolist()
            df = df[self.index_merge + cols]
            df_all = df_all.merge(df, "left", self.index_merge)
            if df_all[cols].sum(numeric_only=True).sum() == 0:
                raise ValueError(
                    "No data in %s \n %s \n %s" % (cols, df.head(), df_all.head())
                )

        # Join other sheets if requested
        if other_element is not None:
            other_sheets = self.sheets[self.sheets["product"] == "other"]
            other_sheets = other_sheets[other_sheets["element"].isin(other_element)]
            for name in other_sheets.index:
                df = self.get_sheet_long(name)
                element = other_sheets.loc[name]["element"]
                cols = df.columns[df.columns.str.match("^" + element)].tolist()
                # Remove the product name from the join index
                index = self.index_merge.copy()
                index.remove("faostat_name")
                df = df[index + cols]
                df_all = df_all.merge(df, "left", index)

        # Set an index
        df_all.set_index(self.index, inplace=True)
        return df_all

    def get_country_rows(self, *args, **kwargs):
        """Get only the country rows from the joint_sheets method"""
        df = self.join_sheets(*args, **kwargs)
        selector = df.index.isin(self.country_aggregates, level="country")
        # Copy the slices to new data frames to avoid the warning:
        #   "A value is trying to be set on a copy of a slice from a DataFrame.
        #   Try using .loc[row_indexer,col_indexer] = value instead"
        return df[~selector].copy()

    def get_agg_rows(self, *args, **kwargs):
        """Get only the aggregated rows from the join_sheets method

        Aggregates are world and continents.
        """
        df = self.join_sheets(*args, **kwargs)
        selector = df.index.isin(self.country_aggregates, level="country")
        return df[selector].copy()

    def get_names(self):
        """Get the product and country names from the names sheet"""
        csv_file_name = self.input_dir / "names.csv"
        # Headers are on two columns, load them, merge them and convert to lower case
        df = pandas.read_csv(csv_file_name, header=[0, 1])
        df.columns = [str("_".join(col)).lower() for col in df.columns]
        df.rename(
            columns=lambda x: re.sub(r"unnamed_\d+_", "", str(x)).lower(), inplace=True
        )
        df.rename(columns=lambda x: re.sub(r"_\d+_", "_", str(x)).lower(), inplace=True)
        return df

    def get_country_groups(self):
        """Get the country grouping by continents"""
        df = self.get_names()
        df.rename(
            columns={
                "gfpm_x_country": "country",  # Spreadsheet B2018 and B2020
                "faostat_gfpm_x_country": "country",  # Spreadsheet B2021
                "code": "faostat_country_code",
            },
            inplace=True,
        )
        df["region"] = df["region"].str.upper()
        assert set(["country", "region"]).issubset(df.columns)
        return df

    def convert_sheets_to_dataset(
        self, product: str, other_element: [list, str] = None
    ) -> xarray.Dataset:
        """Combine 2D and 1D arrays from all sheet sheet corresponding to the given
        product into an xarray dataset

        Example load sawnwood data, add GDP to the panel data:

            >>> from cobwood.gfpmx_data import gfpmx_data
            >>> sawn = gfpmx_data.convert_sheets_to_dataset("sawn")
            >>> print(sawn.data_vars)
            >>> panel = gfpmx_data.convert_sheets_to_dataset("panel", ["gdp"])

        """
        sheets = self.sheets[self.sheets["product"] == product]
        # Join other sheets if requested
        if other_element is not None:
            other_sheets = self.sheets[self.sheets["product"] == "other"]
            other_sheets = other_sheets[other_sheets["element"].isin(other_element)]
            sheets = pandas.concat([sheets, other_sheets])
        # Create a dataset for this product
        ds = xarray.Dataset()
        # Add metadata
        ds.attrs["product"] = product
        # Load all sheets for this product
        for this_sheet in sheets.index:
            if this_sheet in ["author", "names", "notes", "worldprice"]:
                continue
            try:
                df = self.get_sheet_wide(this_sheet)
            except pandas.errors.EmptyDataError:
                print(f"The '{this_sheet}' sheet doesn't contain any data.")
                continue
            if "country" not in df.columns:
                print(f"The '{this_sheet}' sheet doesn't have a country column.")
                continue
            element = sheets.loc[this_sheet]["element"]
            # Add the 2D array to the dataset
            ds[element] = convert_to_2d_array(df)
            # Add the 1D arrays to the dataset
            # If `coef_keywords` are in the column names
            # Note: trend and stock elasticity are defined for the World only
            # and could be stored as an attribute, we keep them as a 1D array
            # for now.
            coef_keywords = "elast|const|marginal|rate|stock|trend"
            coefficients = df.columns[df.columns.str.contains(coef_keywords)]
            for col in coefficients:
                # coerce to a numeric value
                df[col] = pandas.to_numeric(df[col], errors="coerce")
                ds[element + "_" + col] = convert_to_1d_array(df, col)
        check_variable_presence(ds)
        # Add region data on continents to be used for groupings
        region_data = self.country_groups.set_index("country")["region"]
        ds["region"] = xarray.DataArray.from_series(region_data)
        # Add country boolean to be used for computations with `loc`
        ds["c"] = ~ds.region.isnull()
        return ds
