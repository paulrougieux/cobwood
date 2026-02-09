"""Plot GFPMx dataset objects by region (continent) or by country"""

import seaborn
import xarray
from typing import Optional, List


def plot_da_by_region(
    ds: xarray.Dataset, da_name: str
) -> xarray.plot.facetgrid.FacetGrid:
    """Plot a data array by region given a dataset and the name of the data array inside it.

    Example:

        from cobwood.gfpmx import GFPMX
        from cobwood.gfpmx_plot import plot_da_by_region
        gfpmxb2021 = GFPMX(scenario="base_2021", rerun=False)
        plot_da_by_region(gfpmxb2021["indround"], "prod")

    Note that this plotting function is also available as a method of the GFPMX
    object.

    """
    return ds[da_name].loc[~ds.c].plot(col="country", col_wrap=4)


def facet_plot_by_var(
    ds: xarray.Dataset,
    variables: Optional[List[str]] = None,
    countries: Optional[List[str]] = None,
    ylabel: Optional[str] = None,
    title: Optional[str] = None,
    ncol: int = 2,
) -> seaborn.axisgrid.FacetGrid:
    """Plot the given dataset variables with a facet for each variable and a
    color line for each continent

    Example:

        from cobwood.gfpmx import GFPMX
        from cobwood.gfpmx_plot import facet_plot_by_var
        gfpmxb2021 = GFPMX(scenario="base_2021", rerun=False)
        # By default plot one line by continent
        facet_plot_by_var(gfpmxb2021.indround)
        # The country argument can specify one line by country
        facet_plot_by_var(gfpmxb2021.indround, countries=["Canada", "France", "Japan"])
        # Plot Forest area and forest stock
        facet_plot_by_var(gfpmxb2021.other, ["area", "stock"],
                      ylabel="Area in 1000ha and stock in million m3")

    """
    if variables is None:
        variables = ["cons", "imp", "exp", "prod", "price"]
    if ylabel is None:
        ylabel = "Quantity in 1000 m3, price in USD/m3"
    if title is None:
        title = ds.product
    # Keep only the selected variables
    if countries is None:
        # Select continents
        df = ds.loc[{"country": ~ds.c}][variables].to_dataframe()
    else:
        # Select countries
        df = ds.loc[{"country": countries}][variables].to_dataframe()
    df = df.reset_index().melt(id_vars=["country", "year"])
    g = seaborn.relplot(
        data=df,
        x="year",
        y="value",
        col="variable",
        hue="country",
        kind="line",
        col_wrap=ncol,
        height=3,
        facet_kws={"sharey": False, "sharex": False},
    )
    g.set(ylim=(0, None))
    g.set_ylabels("")
    g.fig.supylabel(ylabel)
    g.fig.suptitle(title)
    g.fig.subplots_adjust(left=0.15, top=0.85)
    # Use scientific notation on y-axis
    for ax in g.axes.flat:
        ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 4))
    return g
