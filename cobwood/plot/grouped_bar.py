"""Grouped bar chart comparing consumption, production, import and export by region."""

import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import xarray

from cobwood.plot import to_million_m3


# Default variable display names and colors, in canonical order
_VAR_LABELS = {
    "cons": "Consumption",
    "prod": "Production",
    "imp": "Import",
    "exp": "Export",
}

_VAR_COLORS = {
    "cons": "#4878CF",
    "prod": "#6ACC65",
    "imp": "#D65F5F",
    "exp": "#B47CC7",
}


def grouped_bar(
    ds: xarray.Dataset,
    year: int = 2021,
    vars: list = None,
) -> matplotlib.figure.Figure:
    """Plot a grouped bar chart of forest product flows by region for a single year.

    Regional aggregates (continents) are extracted from the country dimension
    where ``ds.c == False``. Each region is shown as a group of bars, one bar
    per variable (consumption, production, import, export). Regions are sorted
    by descending production value. Value labels are drawn on top of each bar
    when they fit within the figure.

    Parameters
    ----------
    ds : xarray.Dataset
        Xarray Dataset for a single forest product (e.g. sawnwood). Must
        contain a boolean variable ``c`` (True = individual country, False =
        continent/region) and the variables listed in ``vars``.
    year : int, optional
        Year for which to plot the data, by default ``2021``.
    vars : list of str, optional
        Variables to include as bars within each group. When ``None``, defaults
        to ``["cons", "prod", "imp", "exp"]`` filtered to those actually present
        in ``ds``.

    Returns
    -------
    matplotlib.figure.Figure
        The matplotlib Figure object containing the grouped bar chart.

    Example
    -------
    >>> from cobwood.gfpmx import GFPMX
    >>> from cobwood.plot import grouped_bar
    >>> gfpmxb2021 = GFPMX(scenario="base_2021", rerun=False)
    >>> fig = grouped_bar(gfpmxb2021["sawn"], year=2021)
    >>> fig.savefig(gfpmxb2021.plot_dir / "grouped_bar.png", bbox_inches="tight")
    """
    # Resolve variables
    default_vars = ["cons", "prod", "imp", "exp"]
    if vars is None:
        vars = [v for v in default_vars if v in ds.variables]
    else:
        missing = [v for v in vars if v not in ds.variables]
        if missing:
            raise ValueError(
                f"Variable(s) {missing} not found in dataset. "
                f"Available variables: {list(ds.data_vars)}"
            )

    if not vars:
        raise ValueError("No plottable variables found in dataset.")

    # Select regional aggregates and the requested year
    ds_regions = ds.loc[{"country": ~ds.c}]

    # Build a DataFrame with one row per region
    df = ds_regions[vars].to_dataframe()[vars].reset_index()
    df = df[df["year"] == year].drop(columns="year")
    df = df.dropna(subset=vars, how="all")

    if df.empty:
        raise ValueError(f"No regional data found for year {year}.")

    # Sort regions by production if available, otherwise first var
    sort_var = "prod" if "prod" in vars else vars[0]
    df = df.sort_values(sort_var, ascending=False).reset_index(drop=True)

    regions = df["country"].tolist()
    n_regions = len(regions)
    n_vars = len(vars)

    # Bar geometry
    group_width = 0.7
    bar_width = group_width / n_vars
    offsets = np.linspace(
        -(group_width - bar_width) / 2,
        (group_width - bar_width) / 2,
        n_vars,
    )
    x = np.arange(n_regions)

    # Unit from the first available variable
    unit = ds[vars[0]].attrs.get("unit", "1000 m3")
    if unit in ("1000 m3", "1000m3"):
        for v in vars:
            df[v] = to_million_m3(df[v])
        unit = "million m3"
    product = ds.attrs.get("product", "")

    fig, ax = plt.subplots(figsize=(max(10, n_regions * 1.4), 6))

    bars_all = []
    for i, var in enumerate(vars):
        values = df[var].values
        color = _VAR_COLORS.get(var, None)
        label = _VAR_LABELS.get(var, var.capitalize())
        bars = ax.bar(
            x + offsets[i],
            values,
            width=bar_width,
            label=label,
            color=color,
            edgecolor="white",
            linewidth=0.4,
        )
        bars_all.append((bars, values))

    # Value labels on top of each bar if they fit
    # Determine a font size scaled to bar width in display units
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    ax_width_px = ax.get_window_extent(renderer=renderer).width
    bar_width_px = ax_width_px / (n_regions * n_vars + 2)
    label_fontsize = max(5, min(8, bar_width_px / 10))

    y_max = ax.get_ylim()[1]
    for bars, values in bars_all:
        for bar, val in zip(bars, values):
            if np.isnan(val) or val <= 0:
                continue
            bar_top = bar.get_height()
            # Only label if there is vertical clearance (at least 4% of axis range)
            if bar_top > 0.04 * y_max:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar_top * 1.005,
                    f"{val:,.0f}",
                    ha="center",
                    va="bottom",
                    fontsize=label_fontsize,
                    rotation=90 if bar_width_px < 30 else 0,
                    clip_on=True,
                )

    ax.set_xticks(x)
    ax.set_xticklabels(regions, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel(unit)
    ax.set_ylim(bottom=0, top=ax.get_ylim()[1] * 1.12)

    title_parts = [product.capitalize()] if product else []
    title_parts.append(f"Market flows by region — {year}")
    ax.set_title(" — ".join(title_parts) if len(title_parts) > 1 else title_parts[0])

    ax.legend(
        loc="upper right",
        fontsize=9,
        frameon=True,
    )
    ax.yaxis.set_major_formatter(
        plt.matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}")
    )

    fig.tight_layout()
    return fig
