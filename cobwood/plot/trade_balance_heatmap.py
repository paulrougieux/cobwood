"""Trade balance matrix heatmap: net trade by country × product at a given year."""

from __future__ import annotations

import matplotlib.figure
import matplotlib.pyplot as plt
import pandas
import seaborn
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cobwood.gfpmx import GFPMX

from cobwood.plot import to_million_m3


def trade_balance_heatmap(
    model: GFPMX,
    year: int = 2021,
    top_n: int = 40,
) -> matplotlib.figure.Figure:
    """Plot a heatmap of net trade by country (rows) and product (columns).

    Each cell shows the net trade value for one country–product combination at
    the requested year.  Only individual countries (``ds.c == True``) are
    included.  The colour scale runs from dark red (large net importer, most
    negative) through white (balanced) to dark blue (large net exporter, most
    positive), centred at zero.

    Countries are ranked by their total absolute net trade summed across all
    products, and only the top *top_n* countries are displayed so that the
    chart remains readable.

    Parameters
    ----------
    model : GFPMX
        A GFPMX model object.  Each product dataset is accessed via
        ``model[product]`` and must expose a ``nettrade`` variable as well as
        the boolean country-flag variable ``c``.
    year : int, optional
        The year at which net trade values are extracted.  Values at or below
        2021 are considered historical; values above 2021 are projections.
        Default is ``2021``.
    top_n : int, optional
        Maximum number of countries to display, selected by descending total
        absolute net trade across all products.  Default is ``40``.

    Returns
    -------
    matplotlib.figure.Figure
        The matplotlib Figure containing the heatmap.

    Example
    -------
    >>> from cobwood.gfpmx import GFPMX
    >>> from cobwood.plot import trade_balance_heatmap
    >>> gfpmxb2021 = GFPMX(scenario="base_2021", rerun=False)
    >>> fig = trade_balance_heatmap(gfpmxb2021, year=2021, top_n=40)
    >>> fig.savefig(gfpmxb2021.plot_dir / "trade_balance_heatmap.png", bbox_inches="tight")
    """
    # Collect one series per product: index = country name, value = nettrade
    series_list = []
    unit = "1000m3"  # fallback default

    for product in model.products:
        ds = model[product]

        # Individual countries only
        ds_countries = ds.loc[{"country": ds.c}]

        # Extract nettrade at the requested year
        da = ds_countries["nettrade"].sel(year=year)

        # Keep track of the unit from the first product that declares one
        detected_unit = da.attrs.get("unit", "")
        if detected_unit:
            unit = detected_unit

        s = da.to_series()
        s.name = product
        series_list.append(s)

    # Build wide DataFrame: rows = countries, columns = products
    df = pandas.concat(series_list, axis=1)

    # Drop countries that are entirely NaN across all products
    df = df.dropna(how="all")

    # Select top_n countries by total absolute net trade
    total_abs = df.abs().sum(axis=1)
    top_countries = total_abs.nlargest(top_n).index
    df = df.loc[top_countries]

    # Sort countries so the largest net exporters appear at the top and the
    # largest net importers at the bottom (descending total signed net trade)
    total_signed = df.sum(axis=1)
    df = df.loc[total_signed.sort_values(ascending=False).index]

    # Fill remaining NaN with 0 for display purposes only
    df_plot = df.fillna(0)

    if unit in ("1000 m3", "1000m3"):
        df_plot = to_million_m3(df_plot)
        unit = "million m3"

    # Determine a symmetric colour scale so that 0 maps to white
    abs_max = df_plot.abs().max().max()
    if abs_max == 0:
        abs_max = 1  # avoid degenerate scale

    # Figure dimensions: grow with number of countries
    n_countries = len(df_plot)
    n_products = len(model.products)
    fig_height = max(8, n_countries * 0.28)
    fig_width = max(7, n_products * 1.4)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    seaborn.heatmap(
        df_plot,
        ax=ax,
        cmap="RdBu",
        center=0,
        vmin=-abs_max,
        vmax=abs_max,
        linewidths=0.3,
        linecolor="white",
        cbar_kws={
            "shrink": 0.6,
            "label": f"Net Trade ({unit})",
        },
    )

    period_label = "Historical" if year <= 2021 else "Projected"
    ax.set_title(
        f"Trade Balance Matrix — {period_label} {year}\n"
        f"(Top {n_countries} countries by absolute net trade; "
        f"blue = net exporter, red = net importer)",
        pad=14,
        fontsize=11,
    )
    ax.set_xlabel("Product", labelpad=8)
    ax.set_ylabel("Country", labelpad=8)
    ax.tick_params(axis="x", rotation=30, labelsize=9)
    ax.tick_params(axis="y", rotation=0, labelsize=8)

    fig.tight_layout()
    return fig
