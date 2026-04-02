"""Parallel coordinates plot showing country clusters across elasticity parameters."""

from typing import List, Optional

import matplotlib.cm as cm
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import xarray


# Canonical ordered list of elasticity / structural variables to display
_ELASTICITY_VARS = [
    "cons_price_elasticity",
    "cons_gdp_elasticity",
    "imp_price_elasticity",
    "imp_gdp_elasticity",
    "exp_marginal_propensity_to_export",
    "price_stock_elast",
    "price_world_price_elasticity",
    "price_input_elast",
    "tariff",
]

# Short axis labels for readability
_SHORT_LABELS = {
    "cons_price_elasticity": "Cons\nprice\nelast.",
    "cons_gdp_elasticity": "Cons\nGDP\nelast.",
    "imp_price_elasticity": "Imp\nprice\nelast.",
    "imp_gdp_elasticity": "Imp\nGDP\nelast.",
    "exp_marginal_propensity_to_export": "Exp\nprop.\nexport",
    "price_stock_elast": "Price\nstock\nelast.",
    "price_world_price_elasticity": "Price\nworld\nelast.",
    "price_input_elast": "Price\ninput\nelast.",
    "tariff": "Tariff",
}


def parallel_coordinates(
    ds: xarray.Dataset,
    year: int = 2021,
    vars: Optional[List[str]] = None,
) -> matplotlib.figure.Figure:
    """Parallel coordinates plot of country elasticity parameters.

    Each line represents one country. Lines are coloured by quintile of
    consumption at the selected year, so high- and low-consuming countries can
    be visually distinguished. Each axis is independently normalised to [0, 1]
    so parameters with very different magnitudes are directly comparable.
    Countries with any missing value in the selected variables are silently
    dropped. The five countries with the highest consumption are labelled on the
    right-hand axis.

    Parameters
    ----------
    ds : xarray.Dataset
        Xarray Dataset for a single forest product (e.g. sawnwood). Must
        contain a boolean variable ``c`` (True = individual country, False =
        continent/region). Elasticity variables and ``cons`` are expected as
        data variables.
    year : int, optional
        Year at which to extract parameter values. Defaults to ``2021``.
    vars : list of str, optional
        Explicit list of variable names to show as axes. When ``None``, all
        elasticity variables from the canonical list that are present in *ds*
        are used automatically.

    Returns
    -------
    matplotlib.figure.Figure
        The matplotlib Figure containing the parallel coordinates chart.

    Raises
    ------
    ValueError
        If none of the requested variables are available in *ds*, or if fewer
        than two variables remain after filtering.

    Example
    -------
    >>> from cobwood.gfpmx import GFPMX
    >>> from cobwood.plot import parallel_coordinates
    >>> gfpmxb2021 = GFPMX(scenario="base_2021", rerun=False)
    >>> fig = parallel_coordinates(gfpmxb2021["sawn"], year=2021)
    >>> fig.savefig(gfpmxb2021.plot_dir / "parallel_coordinates.png", bbox_inches="tight")
    """
    # ------------------------------------------------------------------ #
    # Resolve variable list                                                #
    # ------------------------------------------------------------------ #
    if vars is None:
        selected_vars = [v for v in _ELASTICITY_VARS if v in ds.variables]
    else:
        missing = [v for v in vars if v not in ds.variables]
        if missing:
            raise ValueError(
                f"Variable(s) not found in dataset: {missing}. "
                f"Available variables: {sorted(ds.data_vars)}"
            )
        selected_vars = list(vars)

    if len(selected_vars) < 2:
        raise ValueError(
            "At least two variables are required for a parallel coordinates plot. "
            f"Found: {selected_vars}"
        )

    # Drop variables where >50% of individual countries have NaN (e.g. price_stock_elast)
    countries_mask = ds.c
    selected_vars = [
        v
        for v in selected_vars
        if float((~ds[v].loc[{"country": countries_mask}].isnull()).mean()) >= 0.5
    ]
    if len(selected_vars) < 2:
        raise ValueError(
            "Fewer than 2 variables with sufficient data for individual countries."
        )

    # ------------------------------------------------------------------ #
    # Extract data for individual countries at the requested year         #
    # ------------------------------------------------------------------ #
    ds_countries = ds.loc[{"country": ds.c}]

    # Build a DataFrame with one row per country.
    # Some variables (elasticities) have only a country dim; others (tariff,
    # cons) also have a year dim.  Extract each group separately and merge.
    all_vars = selected_vars + (["cons"] if "cons" in ds.variables else [])
    has_year = [v for v in all_vars if "year" in ds_countries[v].dims]
    no_year = [v for v in all_vars if "year" not in ds_countries[v].dims]

    frames = []
    if has_year:
        frames.append(
            ds_countries[has_year]
            .sel(year=year, method="nearest")
            .to_dataframe()
            .reset_index()[["country"] + has_year]
        )
    if no_year:
        frames.append(
            ds_countries[no_year].to_dataframe().reset_index()[["country"] + no_year]
        )

    if not frames:
        raise ValueError("No data could be extracted.")

    df = frames[0]
    for other in frames[1:]:
        df = df.merge(other, on="country", how="outer")

    # Drop countries with any NaN in the elasticity columns
    df = df.dropna(subset=selected_vars).reset_index(drop=True)

    if df.empty:
        raise ValueError(
            f"No countries with complete data for all selected variables at year={year}."
        )

    # ------------------------------------------------------------------ #
    # Colour by quintile of consumption                                   #
    # ------------------------------------------------------------------ #
    if "cons" in df.columns and df["cons"].notna().any():
        df["_quintile"] = (
            df["cons"]
            .rank(method="first", na_option="bottom")
            .transform(lambda r: np.ceil(r / len(df) * 5).clip(1, 5))
            .astype(int)
        )
    else:
        df["_quintile"] = 3  # neutral mid-quintile when cons is unavailable

    cmap = cm.get_cmap("RdYlGn", 5)
    quintile_colors = {q: cmap(q - 1) for q in range(1, 6)}

    # ------------------------------------------------------------------ #
    # Normalise each variable to [0, 1]                                   #
    # ------------------------------------------------------------------ #
    df_norm = df.copy()
    axis_ticks = {}  # store (min, max) for each variable for tick labelling

    for v in selected_vars:
        col = df[v].values.astype(float)
        v_min, v_max = col.min(), col.max()
        axis_ticks[v] = (v_min, v_max)
        span = v_max - v_min
        df_norm[v] = (col - v_min) / span if span != 0 else np.zeros_like(col)

    # ------------------------------------------------------------------ #
    # Build figure                                                         #
    # ------------------------------------------------------------------ #
    n_axes = len(selected_vars)
    fig, host = plt.subplots(figsize=(max(10, n_axes * 1.6), 7))

    # x positions for each axis
    x_positions = np.linspace(0, 1, n_axes)

    # Draw one line per country
    for _, row in df_norm.iterrows():
        y_vals = [row[v] for v in selected_vars]
        color = quintile_colors[int(row["_quintile"])]
        host.plot(x_positions, y_vals, color=color, alpha=0.45, linewidth=0.9)

    # ------------------------------------------------------------------ #
    # Draw vertical axes with tick marks and labels                       #
    # ------------------------------------------------------------------ #
    host.set_xlim(0, 1)
    host.set_ylim(-0.05, 1.05)
    host.set_xticks(x_positions)
    host.set_xticklabels(
        [_SHORT_LABELS.get(v, v) for v in selected_vars],
        fontsize=8,
        ha="center",
    )
    host.tick_params(axis="x", which="both", length=0, pad=6)
    host.set_yticks([])

    for xp in x_positions:
        host.axvline(x=xp, color="black", linewidth=0.8, alpha=0.6)

    # Min/max raw value labels on each vertical axis
    for xp, v in zip(x_positions, selected_vars):
        v_min, v_max = axis_ticks[v]
        host.text(
            xp,
            -0.04,
            f"{v_min:.3g}",
            ha="center",
            va="top",
            fontsize=6.5,
            color="dimgrey",
            transform=host.transData,
        )
        host.text(
            xp,
            1.04,
            f"{v_max:.3g}",
            ha="center",
            va="bottom",
            fontsize=6.5,
            color="dimgrey",
            transform=host.transData,
        )

    # ------------------------------------------------------------------ #
    # Label the top-5 countries by consumption on the last axis          #
    # ------------------------------------------------------------------ #
    if "cons" in df.columns and df["cons"].notna().any():
        top5_idx = df["cons"].nlargest(5).index
    else:
        top5_idx = df.head(5).index

    last_xp = x_positions[-1]
    last_var = selected_vars[-1]
    for idx in top5_idx:
        y_norm = df_norm.loc[idx, last_var]
        country_name = df.loc[idx, "country"]
        host.annotate(
            country_name,
            xy=(last_xp, y_norm),
            xytext=(last_xp + 0.02, y_norm),
            fontsize=7,
            va="center",
            color="black",
            annotation_clip=False,
        )

    # ------------------------------------------------------------------ #
    # Colour legend for quintiles                                          #
    # ------------------------------------------------------------------ #
    cons_unit = (
        ds["cons"].attrs.get("unit", "1000 m3") if "cons" in ds.variables else ""
    )
    legend_patches = [
        plt.matplotlib.patches.Patch(
            facecolor=quintile_colors[q],
            label=f"Q{q} cons. {'(lowest)' if q == 1 else '(highest)' if q == 5 else ''}",
        )
        for q in range(1, 6)
    ]
    legend = host.legend(
        handles=legend_patches,
        title=f"Consumption\nquintile ({cons_unit})",
        loc="upper left",
        bbox_to_anchor=(1.12, 1.0),
        borderaxespad=0,
        fontsize=7.5,
        title_fontsize=7.5,
        frameon=True,
    )

    # ------------------------------------------------------------------ #
    # Title and layout                                                     #
    # ------------------------------------------------------------------ #
    product_name = ds.attrs.get("product", "forest product")
    period_label = "projected" if year > 2021 else "historical"
    host.set_title(
        f"{product_name.capitalize()} — elasticity parameters by country"
        f" ({year}, {period_label})",
        fontsize=11,
        pad=14,
    )
    host.spines["top"].set_visible(False)
    host.spines["right"].set_visible(False)
    host.spines["bottom"].set_visible(False)
    host.spines["left"].set_visible(False)

    fig.tight_layout(rect=[0, 0, 0.88, 1])
    return fig
