#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Paul Rougieux.

JRC biomass Project.
Unit D1 Bioeconomy.

Give access to the dataset from the GFPMX model by Joseph Buongiorno
Originally released on 

The GFPMX dataset is useful to:

1. Obtain elasticities, constants  and other coefficients that cannot be estimated easily
1. Verify the reproducibility of results given in the spreadsheet

See also the script that moves this data from Excel to csv files under
`scripts/gfpmx_data_to_csv.py`
"""

# Build in modules
from pathlib import Path

# Third party modules
import pandas

# Internal modules
from gftmx.data_dir import gftmx_data_dir


class GFPMXData:
    """
    Read data from the GFTMX data set.

    The GFTMX dataset was converted to csv files one for each sheet in the
    original Excel Spreadsheet. This singleton gives access to each file.

    Load sawnwood consumption data:

    >>> from gftmx.gfpmx_data import gfpmx_data
    >>> swd_cons = gfpmx_data['SawnCons']
    >>> swd_cons
    """
    data_dir = Path(gftmx_data_dir) / "gfpmx"

    def __getitem__(self, sheet_name):
        """Return a data frame based on the GFTMX sheet name."""
        return self.get_sheet_long(sheet_name)

    def get_sheet(self, sheet_name):
        """Read a csv file into a pandas data frame"""
        csv_file_name = self.data_dir / (sheet_name + ".csv")
        df = pandas.read_csv(csv_file_name)
        return df

    def get_sheet_long(self, sheet_name):
        """Read a csv file into a pandas data frame and reshape it to long format"""
        df_wide = self.get_sheet(sheet_name=sheet_name)
        # Reshape the years to long format
        df_wide["id"] = df_wide.index
        df = pandas.wide_to_long(df_wide, stubnames='year', i='id', j='year')
        return df


# Make a singleton #
gfpmx_data = GFPMXData()
