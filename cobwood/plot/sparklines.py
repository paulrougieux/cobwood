"""Small multiples / sparklines for forest products market time series."""

import math
from typing import List, Optional

import matplotlib.pyplot as plt
import matplotlib.figure
import xarray

from cobwood.plot import to_million_m3


# Year that separates historical observations from model projections
PROJECTION_START = 2022


def sparklines(
    ds: xarray.Dataset,
    var: str = "cons",
    max_countries: int = 30,
    countries: Optional[List[str]] = None,
    ncols: int = 6,
    base_year: int = 2021,
) -> matplotlib.figure.Figure:
    """Plot a grid of compact time-series (sparklines) for individual countries.

    Each mini chart shows one variable over time for a single country.
    Historical data (year <= *base_year*) is drawn with a solid line;
    projections (year > *base_year*) are drawn with a dashed line and a
    light shaded background so the boundary is immediately visible.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset for a single product (e.g. ``gfpmxb2021["sawn"]``).
        Must contain the variable *var* as a DataArray with dims
        ``(country, year)``.  The boolean coordinate ``ds.c`` identifies
        individual countries (``True``) vs. continent / region aggregates
        (``False``).
    var : str, optional
        Name of the variable to plot (default ``"cons"``).
    max_countries : int, optional
        Maximum number of countries to display.  When *countries* is
        ``None`` the top *max_countries* countries ranked by the value of
        *var* in *base_year* are selected (default 30).
    countries : list of str, optional
        Explicit list of country names to display.  When provided,
        *max_countries* is ignored (default ``None``).
    ncols : int, optional
        Number of columns in the sparkline grid (default 6).
    base_year : int, optional
        Last historical year.  Years up to and including *base_year* are
        drawn as solid lines; years after *base_year* are dashed with a
        shaded background (default 2021).

    Returns
    -------
    matplotlib.figure.Figure
        The matplotlib Figure containing the sparkline grid.

    Example
    -------
    ::

        from cobwood.gfpmx import GFPMX
        from cobwood.plot import sparklines
        gfpmxb2021 = GFPMX(scenario="base_2021", rerun=False)
        fig = sparklines(gfpmxb2021["sawn"], var="cons", max_countries=30)
        fig.savefig(gfpmxb2021.plot_dir / "sparklines.png", bbox_inches="tight")

    """
    if var not in ds.variables:
        raise ValueError(
            f"Variable '{var}' not found in dataset. "
            f"Available variables: {list(ds.data_vars)}"
        )

    da = ds[var]

    # --- Select countries ---------------------------------------------------
    if countries is not None:
        # Use the caller-supplied list directly
        country_list = [c for c in countries if c in da.coords["country"].values]
        if not country_list:
            raise ValueError(
                "None of the requested countries are present in the dataset."
            )
    else:
        # Restrict to individual countries (ds.c == True)
        da_countries = da.loc[{"country": ds.c}]

        # Rank by base-year value and keep top max_countries
        if base_year in da_countries.coords["year"].values:
            base_values = da_countries.sel(year=base_year)
        else:
            # Fall back to the last available year
            base_values = da_countries.isel(year=-1)

        # Drop NaN before sorting
        base_values = base_values.dropna("country")
        ranked = base_values.sortby(base_values, ascending=False)
        country_list = ranked.coords["country"].values[:max_countries].tolist()

    n = len(country_list)
    ncols = min(ncols, n)
    nrows = math.ceil(n / ncols)

    # --- Figure layout -------------------------------------------------------
    fig_width = ncols * 2.2
    fig_height = nrows * 1.6
    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(fig_width, fig_height),
        squeeze=False,
    )

    # Retrieve unit for axis label
    unit = da.attrs.get("unit", "1000 m3")
    convert_volume = unit in ("1000 m3", "1000m3")
    if convert_volume:
        unit = "million m3"

    # Colour used for the main line
    line_color = "#2271b2"
    shade_color = "#f5f0e8"

    for idx, country in enumerate(country_list):
        row, col = divmod(idx, ncols)
        ax = axes[row][col]

        try:
            series = da.sel(country=country).to_series().dropna()
        except KeyError:
            ax.set_visible(False)
            continue

        if series.empty:
            ax.set_visible(False)
            continue

        years = series.index.astype(int)
        values = series.values
        if convert_volume:
            values = to_million_m3(values)

        # Split into historical and projected segments
        hist_mask = years <= base_year
        proj_mask = years > base_year

        # Shaded background for projected region
        if proj_mask.any():
            ax.axvspan(
                base_year + 0.5,
                years[proj_mask].max() + 0.5,
                color=shade_color,
                zorder=0,
            )

        # Historical segment — solid line
        if hist_mask.any():
            ax.plot(
                years[hist_mask],
                values[hist_mask],
                color=line_color,
                linewidth=0.9,
                solid_capstyle="round",
            )

        # Projected segment — dashed; connect to last historical point for
        # a smooth visual join
        if proj_mask.any():
            proj_years = years[proj_mask]
            proj_values = values[proj_mask]

            # Prepend the last historical point so there is no visual gap
            if hist_mask.any():
                join_year = years[hist_mask][-1]
                join_value = values[hist_mask][-1]
                proj_years = [join_year] + list(proj_years)
                proj_values = [join_value] + list(proj_values)

            ax.plot(
                proj_years,
                proj_values,
                color=line_color,
                linewidth=0.9,
                linestyle="--",
                dashes=(3, 2),
                solid_capstyle="round",
            )

        # Mark the base year with a thin vertical reference line
        if base_year in years:
            ax.axvline(base_year, color="#aaaaaa", linewidth=0.6, linestyle=":")

        # --- Sparkline styling: minimal chrome ---
        ax.set_title(country, fontsize=6.5, pad=2, fontweight="bold")
        ax.tick_params(labelsize=5, length=2, width=0.5, pad=1)
        ax.xaxis.set_major_locator(plt.MaxNLocator(3, integer=True))
        ax.yaxis.set_major_locator(plt.MaxNLocator(3))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        for spine in ax.spines.values():
            spine.set_linewidth(0.5)
            spine.set_color("#cccccc")
        ax.set_ylim(bottom=0)

    # Hide any unused subplot cells
    for idx in range(n, nrows * ncols):
        row, col = divmod(idx, ncols)
        axes[row][col].set_visible(False)

    # --- Figure-level labels and title --------------------------------------
    # Determine product name from dataset attrs if available
    product_label = ds.attrs.get("product", var)
    fig.suptitle(
        f"{product_label} — {var}  [{unit}]",
        fontsize=9,
        fontweight="bold",
        y=1.01,
    )

    # Single shared x/y axis labels via fig.text
    fig.text(
        0.5,
        -0.01,
        "Year",
        ha="center",
        va="top",
        fontsize=7,
        color="#555555",
    )
    fig.text(
        -0.01,
        0.5,
        unit,
        ha="right",
        va="center",
        fontsize=7,
        color="#555555",
        rotation=90,
    )

    fig.tight_layout(pad=0.6, h_pad=1.2, w_pad=0.8)
    return fig
