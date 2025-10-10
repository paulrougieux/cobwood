"""Prepare FAOSTAT data for forest sector modelling


Note:
- The problem is that this requires the biotrade package and the biotrade_data
  directory to be defined so that the intermediate download can be saved.

"""

from functools import cached_property
from biotrade.faostat import faostat as biotrade_faostat


class FAOSTAT:
    """Download faostat data and prepare it as N dimentional Xarray data

    >>> from cobwood.faostat import faostat
    >>> fp = faostat.forestry_production_df
    >>> faostat.forestry_production_ds

    TODO: Make a dataset for sawnwood elements

    # Create a dataset
    ds = xarray.Dataset()
    selector = fp["product"] == "sawnwood"
    df = fp.loc[selector].copy()
    for element in df["element"].unique():
        selector = fp["element"] == element
        df_var = df.loc[element]
        print(element)
        # Add the data array to the dataset

    """

    def __init__(self):
        pass

    @cached_property
    def forestry_production_df(self):
        """Forestry production pandas dataframe"""
        return biotrade_faostat.pump.read_df("forestry_production")

    def foresty_production_ds(self):
        """Forestry production Xarray Dataset"""


# Make a singleton
faostat = FAOSTAT()
