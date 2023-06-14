"""Plot GFPMx dataset objects by region (continent) or by country

"""

import seaborn
import xarray


def plot_da_by_region(
    ds: xarray.Dataset, da_name: str
) -> xarray.plot.facetgrid.FacetGrid:
    """Plot a data array by region given a dataset and the name of the data array inside it.

    Example:

        >>> from cobwood.gfpmx_data import GFPMXData
        >>> from cobwood.gfpmx_plot import plot_da_by_region
        >>> gfpmx_base_2020 = GFPMXData(data_dir="gfpmx_base2020", base_year=2020)
        >>> plot_da_by_region(gfpmx_base_2020["indround"], "prod")

    """
    return ds[da_name].loc[~ds.c].plot(col="country", col_wrap=4)


def plot_ds_by_davar(
    ds: xarray.Dataset, da_vars: list = None
) -> seaborn.axisgrid.FacetGrid:
    """Plot the given dataset variables with a facet for each variable and a
    color line for each continent

    Example:

        >>> from cobwood.gfpmx_data import GFPMXData
        >>> from cobwood.gfpmx_plot import plot_ds_by_davar
        >>> gfpmx_base_2020 = GFPMXData(data_dir="gfpmx_base2020", base_year=2020)
        >>> plot_ds_by_davar(gfpmx_base_2020.indround)

    """
    if da_vars is None:
        da_vars = ["cons", "imp", "exp", "prod", "price"]
    df = ds.loc[{"country": ~ds.c}][da_vars].to_dataframe()
    df = df.reset_index().melt(id_vars=["country", "year"])
    grid = seaborn.relplot(
        data=df,
        x="year",
        y="value",
        col="variable",
        hue="country",
        kind="line",
        col_wrap=5,
        height=3,
        facet_kws={"sharey": False, "sharex": False},
    )
    grid.fig.supylabel("Quantity in 1000 m3, price in USD/m3")
    grid.fig.subplots_adjust(left=0.28)
    grid.set(ylim=(0, None))
    return grid
