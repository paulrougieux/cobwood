"""Prepare FAOSTAT data for forest sector modelling


Note:

- `faostat.forestry_production_df` requires the
  [biotrade](https://pypi.org/project/biotrade/) package and the
  `biotrade_data` directory to be defined so that the intermediate download can
  be saved.

"""
from functools import cached_property
from biotrade.faostat import faostat as biotrade_faostat
import pandas as pd
import xarray as xr


class FAOSTAT:
    """Download faostat data and prepare it as N dimentional
    Xarray data

    from cobwood.faostat import faostat
    fp = faostat.forestry_production_df
    ds = faostat.forestry_production_ds

    TODO: Make a dataset for sawnwood elements

    # Create a dataset
    ds = xarray.Dataset()
    selector = fp["product"] == "sawnwood"
    df = fp.loc[selector].copy()
    for element in df["element"].unique():
        print(element)
        selector = df["element"] == element
        df_e = df.loc[selector]
        # Add the data array to the dataset
    """

    def __init__(self) -> None:
        pass

    @cached_property
    def forestry_production_df(self) -> pd.DataFrame:
        """Forestry production pandas dataframe"""
        return biotrade_faostat.pump.read_df("forestry_production")

    @cached_property
    def forestry_production_ds(self) -> xr.Dataset:
        """Forestry production Xarray Dataset"""
        df = self.forestry_production_df
        ds = xr.Dataset()
        for element in df["element"].unique():
            # TODO: replace the product names by shorter product names usable as modelling variables.
            # There should be a mapping to short names and product codes.
            df_elem = df[df["element"] == element].set_index(
                ["reporter", "product", "year"]
            )["value"]
            da = df_elem.to_xarray()
            ds[element] = da
        return ds


# Make a singleton
faostat = FAOSTAT()
