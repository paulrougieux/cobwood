#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Paul Rougieux.

JRC biomass Project.
Unit D1 Bioeconomy.

Give access to the dataset from the GFPMX model by Joseph Buongiorno.
Originally released at
    https://buongiorno.russell.wisc.edu/gfpm/

"""

# Built in modules
import re

# Third party modules
import pandas

# Internal modules
from gftmx.data_dir import gftmx_data_dir


class GFPMXData:
    """
    Read data from the GFTMX data set.

    The GFTMX dataset was converted to csv files one for each sheet in the
    original Excel Spreadsheet. This singleton gives access to each file.

    Load sawnwood consumption data in long format:

        >>> from gftmx.gfpmx_data import gfpmx_data
        >>> swd_cons = gfpmx_data['sawncons']
        >>> swd_cons

    The GFPMX dataset is useful to:

    1. Obtain elasticities, constants and other coefficients that cannot be estimated easily
    1. Verify the reproducibility of results given in the spreadsheet

    See also the script that moves data from the original Excel spreadsheet to csv files:
    `scripts/gfpmx_data_to_csv.py`
    """
    # Location of the csv files
    data_dir = gftmx_data_dir / "gfpmx"

    # Simulation base year i.e. last year of historical data available in the spreadsheet
    base_year = 2018

    def __getitem__(self, sheet_name):
        """Return a data frame based on the GFPMX sheet name."""
        return self.get_sheet_long(sheet_name)

    def __init__(self):
        self.sheets = self.list_sheets()
        self.index_merge = ["year", "country", "faostat_name"]
        self.index = ["year", "country"]

    def list_sheets(self):
        """List sheets available in the GFPMX data folder

        :return data frame with the sheet name, product and element

        For example show all sheets available

            >>> from gftmx.gfpmx_data import gfpmx_data
            >>> from pandas.errors import EmptyDataError
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

            >>> for s in sheets.query("product == 'round'").index:
            >>>     print(gfpmx_data[s].columns.tolist())

        Display the shape of the other sheets

            >>> for s in sheets.query("product == 'other'").index:
            >>>     try:
            >>>         print(s, gfpmx_data[s].shape)
            >>>     except EmptyDataError:
            >>>         print(f"No data in the '{s}' file.")

        """
        sheet_paths =  self.data_dir.glob('**/*.csv')
        df = pandas.DataFrame({"file_name": [x.name for x in sheet_paths]})
        df["name"] = df.file_name.str.extract(f"(.*).csv")
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
        """Read a csv file into a pandas data frame"""
        csv_file_name = self.data_dir / (sheet_name + ".csv")
        df = pandas.read_csv(csv_file_name)
        return df

    def get_sheet_long(self, sheet_name, keep_all_columns = True):
        """Read a csv file into a pandas data frame and reshape it to long format

        Example use

            >>> from gftmx.gfpmx_data import gfpmx_data
            >>> print(gfpmx_data.get_sheet_long("sawncons"))
            >>> print(gfpmx_data.get_sheet_long("sawncons", keep_all_columns = False))

        """
        df_wide = self.get_sheet_wide(sheet_name=sheet_name)
        # Reshape year columns to long format
        index = [x for x in df_wide.columns if not re.search("value", x)]
        df = pandas.wide_to_long(df_wide, stubnames='value', i=index, j='year')
        df.reset_index(inplace=True)
        # Rename the value column according to the shorter element part of the
        # file name. Note there is also an element column which we don't use
        # here.
        element = self.sheets.loc[sheet_name, "element"]
        df.rename(columns = {"value": element}, inplace=True)

        # Prefix any columns that are not part of the index,
        # with the short element name
        index = ['faostat_name', 'element', 'unit',  'country', 'year', element]
        other_cols = list(set(df.columns) - set(index))
        other_cols_renamed = [element + "_" + x for x in other_cols]
        mapping = dict(zip(other_cols, other_cols_renamed))
        df.rename(columns = mapping, inplace=True)
        if not keep_all_columns:
            df = df[self.index_merge + other_cols_renamed + [element]]
        return df

    def get_gdp(self, sheet_name='gdp', index=None, var_name='gdp'):
        """ Return a data frame of cleaned GDP values

            >>> from gftmx.gfpmx_data import gfpmx_data
            >>> gfpmx_data.get_gdp()
        """
        if index is None:
            index = ['id', 'year', 'country']
        df = self.get_sheet_long(sheet_name)
        df = df[index + ['value']]
        df.rename(columns={'value': var_name}, inplace=True)
        return df

    def get_price_lag(self, sheet_name, index=None, var_name='price'):
        """ Return a price table with prices shifted by a one year lag

            >>> from gftmx.gfpmx_data import gfpmx_data
            >>> gfpmx_data.get_price_lag('sawnprice')
        """
        if index is None:
            index = ['id', 'year', 'country']
        df = self.get_sheet_long(sheet_name)
        df = df[index + ['value']]
        df.rename(columns={'value': var_name}, inplace=True)
        # Shift prices by a one year lag
        df.set_index('year', inplace=True)
        df[var_name+"_lag"] = df.groupby(['id', 'country'])[var_name].shift()
        df.reset_index(inplace=True)
        return df

    def join_sheets(self, product):
        """
        Merge all related data frames for a given product

        :param str product: selected product
        :return data frame

        For example join all roundwood sheets in one data frame

            >>> from gftmx.gfpmx_data import gfpmx_data
            >>> rwd = gfpmx_data.join_sheets('round')
            >>> rwd.head()

        Join sheets for all available products

            >>> for product in gfpmx_data.sheets["product"].unique():
            >>>     if product == "other":
            >>>         continue
            >>>     print(product)
            >>>     print(gfpmx_data.join_sheets(product).head())

        """
        sheets = self.sheets[self.sheets["product"] == product]
        first_sheet = sheets.index[0]
        df_all = gfpmx_data.get_sheet_long(first_sheet, keep_all_columns = False)
        for sheet in sheets.index[1:]:
            df = gfpmx_data.get_sheet_long(sheet, keep_all_columns = False)
            df_all = df_all.merge(df, "left", self.index_merge)
        df_all.set_index(self.index, inplace=True)
        return df_all

# Make a singleton #
gfpmx_data = GFPMXData()
