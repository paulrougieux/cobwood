"""Stacked area chart showing regional contributions to global production or consumption."""

import matplotlib.figure
import matplotlib.pyplot as plt
import xarray

from cobwood.plot import to_million_m3


def stacked_area(
    ds: xarray.Dataset,
    var: str = "prod",
    base_year: int = 2021,
) -> matplotlib.figure.Figure:
    """Plot a stacked area chart of regional contributions over time.

    Regions (continents) are extracted from the country dimension where
    ``ds.c == False``. The chart visually separates historical data
    (year <= base_year) from the projected period (year > base_year) with a
    vertical dashed line and a shaded projection zone.

    Parameters
    ----------
    ds : xarray.Dataset
        Xarray Dataset for a single forest product (e.g. sawnwood). Must
        contain a boolean variable ``c`` (True = individual country, False =
        continent/region) and the requested ``var``.
    var : str, optional
        Name of the variable to plot, by default ``"prod"``.
    base_year : int, optional
        Last year of historical data. A vertical dashed line is drawn at this
        year and the projection area is shaded, by default ``2021``.

    Returns
    -------
    matplotlib.figure.Figure
        The matplotlib Figure object containing the stacked area chart.

    Example
    -------
    >>> from cobwood.gfpmx import GFPMX
    >>> from cobwood.plot import stacked_area
    >>> gfpmxb2021 = GFPMX(scenario="base_2021", rerun=False)
    >>> fig = stacked_area(gfpmxb2021["sawn"], var="prod")
    >>> fig.savefig(gfpmxb2021.plot_dir / "stacked_area.png", bbox_inches="tight")
    """
    if var not in ds.variables:
        raise ValueError(
            f"Variable '{var}' not found in dataset. "
            f"Available variables: {list(ds.data_vars)}"
        )

    # Select continent/region aggregates only (ds.c == False)
    ds_regions = ds.loc[{"country": ~ds.c}]
    da = ds_regions[var]

    # Convert to DataFrame and drop NaN rows (e.g. year 2071)
    df = da.to_dataframe()[[var]].reset_index()
    df = df.dropna(subset=[var])

    # Pivot to wide format: index=year, columns=country (region names)
    df_wide = df.pivot(index="year", columns="country", values=var)

    years = df_wide.index.values
    region_names = df_wide.columns.tolist()
    values = df_wide.values.T  # shape: (n_regions, n_years)

    unit = da.attrs.get("unit", "1000 m3")
    if unit in ("1000 m3", "1000m3"):
        values = to_million_m3(values)
        unit = "million m3"
    product = ds.attrs.get("product", var)

    fig, ax = plt.subplots(figsize=(12, 6))

    # Draw stacked area
    polys = ax.stackplot(years, values, labels=region_names)

    # Shade the projection period
    proj_start = base_year + 1
    if proj_start <= years[-1]:
        ax.axvspan(
            proj_start,
            years[-1],
            alpha=0.12,
            color="grey",
            label="_projection_zone",
        )

    # Vertical dashed line at the base year boundary
    ax.axvline(
        x=base_year,
        color="black",
        linestyle="--",
        linewidth=1.2,
        label=f"Base year {base_year}",
    )

    # Annotation for projected area
    y_top = ax.get_ylim()[1]
    ax.text(
        base_year + 1,
        y_top * 0.97,
        "Projected",
        ha="left",
        va="top",
        fontsize=9,
        color="grey",
    )

    ax.set_xlabel("Year")
    ax.set_ylabel(unit)
    ax.set_title(f"{product.capitalize()} — {var} by region")
    ax.set_xlim(years[0], years[-1])
    ax.set_ylim(bottom=0)

    # Legend outside the plot area on the right
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
        borderaxespad=0,
        fontsize=8,
        frameon=True,
    )

    fig.tight_layout()
    return fig
