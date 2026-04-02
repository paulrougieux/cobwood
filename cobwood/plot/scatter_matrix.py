"""Scatter matrix / pair plot for forest products market variables across countries."""

import matplotlib.figure
import numpy as np
import seaborn
import xarray


# Default variables to include when the caller passes vars=None
_DEFAULT_VARS = [
    "cons",
    "gdp",
    "cons_price_elasticity",
    "cons_gdp_elasticity",
]

# Variables whose axes should use a log scale when their range spans > 2 orders
# of magnitude (checked at runtime)
_CANDIDATE_LOG_VARS = {"gdp", "cons", "conspercap", "prod", "imp", "exp"}


def scatter_matrix(
    ds: xarray.Dataset,
    year: int = 2021,
    vars: list = None,
) -> matplotlib.figure.Figure:
    """Scatter matrix (pair plot) of market variables across individual countries.

    Draws a seaborn pairplot with regression lines for the selected variables,
    evaluated at a single year for individual countries only (continents /
    aggregate regions are excluded).  Variables whose value range spans more
    than two orders of magnitude are plotted on a log10 scale.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset for a single product (e.g. ``gfpmxb2021["sawn"]``).  Must
        contain at least the coordinate ``country`` and the boolean variable
        ``c`` (True = individual country, False = continent/region).
    year : int, optional
        Year at which to extract the cross-sectional data slice.  Defaults to
        2021 (the typical GFPMX base year).
    vars : list of str, optional
        Variable names to include in the plot.  When *None* the function uses
        ``["cons", "gdp", "cons_price_elasticity", "cons_gdp_elasticity"]``
        filtered to only those that actually exist in *ds*.

    Returns
    -------
    matplotlib.figure.Figure
        The matplotlib Figure produced by seaborn's pairplot.

    Example
    -------
    ::

        from cobwood.gfpmx import GFPMX
        from cobwood.plot import scatter_matrix
        gfpmxb2021 = GFPMX(scenario="base_2021", rerun=False)
        fig = scatter_matrix(gfpmxb2021["sawn"], year=2021)
        fig.savefig(gfpmxb2021.plot_dir / "scatter_matrix.png", bbox_inches="tight")

    """
    # --- resolve variable list -----------------------------------------------
    if vars is None:
        plot_vars = [v for v in _DEFAULT_VARS if v in ds.variables]
    else:
        plot_vars = [v for v in vars if v in ds.variables]

    if not plot_vars:
        raise ValueError(
            "None of the requested variables are present in the dataset. "
            f"Available variables: {list(ds.variables)}"
        )

    # --- extract individual countries at the requested year ------------------
    ds_countries = ds.loc[{"country": ds.c}]

    if year not in ds_countries.coords["year"].values:
        raise ValueError(
            f"year={year} not found in the dataset. "
            f"Available range: {int(ds_countries.coords['year'].min())}–"
            f"{int(ds_countries.coords['year'].max())}"
        )

    ds_slice = ds_countries.sel(year=year)
    df = ds_slice[plot_vars].to_dataframe()

    # Reset MultiIndex if present; keep country as a plain column
    if df.index.name == "country" or "country" in df.index.names:
        df = df.reset_index()
        if "year" in df.columns:
            df = df.drop(columns=["year"])

    df = df.dropna(subset=plot_vars)

    # --- apply log10 transform where the range spans > 2 orders of magnitude --
    log_vars = []
    renamed = {}  # maps original name -> column name used in df
    for var in plot_vars:
        renamed[var] = var  # default: no rename
        if var in _CANDIDATE_LOG_VARS:
            col = df[var].replace(0, np.nan).dropna()
            if len(col) > 1:
                ratio = col.max() / col.min()
                if ratio > 100:  # > 2 orders of magnitude
                    unit = ds[var].attrs.get("unit", "")
                    new_col = f"log10({var})" + (f" [{unit}]" if unit else "")
                    df[new_col] = np.log10(df[var].replace(0, np.nan))
                    df = df.drop(columns=[var])
                    renamed[var] = new_col
                    log_vars.append(new_col)

    # Build the final ordered column list using (possibly renamed) names
    final_cols = [renamed[v] for v in plot_vars]
    # Only keep columns that survived the log transform step
    final_cols = [c for c in final_cols if c in df.columns]

    # --- collect unit labels for axis titles ----------------------------------
    var_labels = {}
    for orig, col in renamed.items():
        if col not in final_cols:
            continue
        if col.startswith("log10("):
            var_labels[col] = col  # label already encodes the transform + unit
        else:
            unit = ds[orig].attrs.get("unit", "")
            var_labels[col] = f"{col} [{unit}]" if unit else col

    # --- build the pair plot --------------------------------------------------
    product = getattr(ds, "product", "")
    title = f"{product} – scatter matrix" if product else "Scatter matrix"
    title += f" ({year}, individual countries, n={len(df)})"

    grid = seaborn.pairplot(
        df[final_cols],
        kind="reg",
        diag_kind="kde",
        plot_kws={
            "scatter_kws": {"alpha": 0.5, "s": 25},
            "line_kws": {"color": "steelblue"},
        },
        diag_kws={"color": "steelblue", "fill": True},
        corner=False,
    )

    # Apply readable axis labels
    n = len(final_cols)
    for i, col in enumerate(final_cols):
        label = var_labels.get(col, col)
        # Bottom row → x-axis labels
        grid.axes[n - 1, i].set_xlabel(label, fontsize=8)
        # Left column → y-axis labels
        grid.axes[i, 0].set_ylabel(label, fontsize=8)

    grid.figure.suptitle(title, y=1.02, fontsize=11)

    return grid.figure
