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

    def list_sheets(self):
        """List sheets available in the GFPMX data folder

        :return data frame with the sheet name, product and element

        For example show all sheets available

            >>> from gftmx.gfpmx_data import gfpmx_data
            >>> gfpmx_data.list_sheets()

        Show sheets related to sawnwood

            >>> gfpmx_data.list_sheets().query("product=='sawn'")

        """
        sheet_paths =  gfpmx_data.data_dir.glob('**/*.csv')
        df = pandas.DataFrame({"file_name": [x.name for x in sheet_paths]})
        df["name"] = df.file_name.str.extract(f"(.*).csv")
        # Place product patterns in a capture group for extraction
        product_pattern = "fuel|indround|panel|paper|pulp|round|sawn"
        df[["product", "element"]] = df.name.str.extract(f"({product_pattern})?(.*)")
        df = df.sort_values(by=["product", "element"])
        return df[["name", "product", "element"]]

    def get_sheet_wide(self, sheet_name):
        """Read a csv file into a pandas data frame"""
        csv_file_name = self.data_dir / (sheet_name + ".csv")
        df = pandas.read_csv(csv_file_name)
        return df

    def get_sheet_long(self, sheet_name):
        """Read a csv file into a pandas data frame and reshape it to long format"""
        df_wide = self.get_sheet_wide(sheet_name=sheet_name)
        # Reshape the years to long format
        df_wide["id"] = df_wide.index
        df = pandas.wide_to_long(df_wide, stubnames='value', i='id', j='year')
        df.reset_index(inplace=True)
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

    def get_cons(self, sheet_name, price_sheet_name, index=None):
        """
        Get a consumption table and join prices and gdp values

        >>> from gftmx.gfpmx_data import gfpmx_data
        >>> gfpmx_data.get_cons('sawncons', 'sawnprice')
        """
        if index is None:
            index = ['id', 'year', 'country']
        df = gfpmx_data.get_sheet_long(sheet_name)
        df = (df
              .merge(gfpmx_data.get_gdp(), 'left', index)
              .merge(gfpmx_data.get_price_lag(price_sheet_name), 'left', index)
              )
        df.drop(columns=['unnamed_1', 'unnamed_2', 'faostat_name', 'price'], inplace=True)
        return df


# Make a singleton #
gfpmx_data = GFPMXData()
