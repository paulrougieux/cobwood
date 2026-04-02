"""Bubble chart visualisation for forest products market data."""

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import xarray

from cobwood.plot import to_million_m3


_VAR_LABELS = {
    "cons": "Consumption",
    "prod": "Production",
    "gdp": "GDP",
    "imp": "Import",
    "exp": "Export",
    "nettrade": "Net trade",
    "price": "Price",
}


def bubble_chart(
    ds: xarray.Dataset,
    year: int = 2021,
    show_regions: bool = False,
    base_year: int = 2021,
) -> matplotlib.figure.Figure:
    """Draw a bubble chart with GDP on the x-axis, consumption on the y-axis,
    and production encoded as the bubble size.

    Bubbles are coloured by net-trade sign: blue for net exporters (nettrade
    >= 0) and red for net importers (nettrade < 0) when showing countries.
    When *show_regions* is ``True`` the continents/regions are shown instead,
    each coloured with a distinct hue from the default matplotlib colour cycle.

    The 15 largest entities (by production) are annotated with their name.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset for a single forest product (e.g. ``gfpmxb2021["sawn"]``).
        Must contain ``cons``, ``prod``, and ``gdp`` variables with dims
        ``(country, year)`` and a boolean coordinate ``c`` where ``True``
        marks individual countries and ``False`` marks continents/regions.
    year : int, optional
        The year slice to visualise.  Defaults to ``2021``.
    show_regions : bool, optional
        If ``True`` show continent/region aggregates instead of individual
        countries.  Defaults to ``False``.
    base_year : int, optional
        The last historical year.  Years beyond this value are labelled as
        "projected".  Defaults to ``2021``.

    Returns
    -------
    matplotlib.figure.Figure
        Matplotlib figure containing the bubble chart.

    Example
    -------

        from cobwood.gfpmx import GFPMX
        from cobwood.plot import bubble_chart
        gfpmxb2021 = GFPMX(scenario="base_2021", rerun=False)
        fig = bubble_chart(gfpmxb2021["sawn"], year=2021, show_regions=False)
        fig.savefig(gfpmxb2021.plot_dir / "bubble_chart_sawn.png", bbox_inches="tight")
        fig = bubble_chart(gfpmxb2021["fuel"], year=2021, show_regions=False)
        fig.savefig(gfpmxb2021.plot_dir / "bubble_chart_fuel.png", bbox_inches="tight")

    """
    # ------------------------------------------------------------------ #
    # Variable availability checks                                         #
    # ------------------------------------------------------------------ #
    for required in ("cons", "prod", "gdp"):
        if required not in ds.variables:
            raise ValueError(
                f"Variable '{required}' is required but not found in dataset. "
                f"Available variables: {sorted(v for v in ds.variables if v not in ds.coords)}"
            )

    has_nettrade = "nettrade" in ds.variables

    # ------------------------------------------------------------------ #
    # Select the right entity slice (countries or regions)                 #
    # ------------------------------------------------------------------ #
    if show_regions:
        ds_sel = ds.loc[{"country": ~ds.c}]
    else:
        ds_sel = ds.loc[{"country": ds.c}]

    # ------------------------------------------------------------------ #
    # Build a flat DataFrame for the requested year                        #
    # ------------------------------------------------------------------ #
    vars_to_fetch = ["cons", "prod", "gdp"]
    if has_nettrade:
        vars_to_fetch.append("nettrade")

    df = (
        ds_sel[vars_to_fetch]
        .sel(year=year, method="nearest")
        .to_dataframe()
        .reset_index()
    )
    df = df.dropna(subset=["cons", "prod", "gdp"])
    df = df[df["prod"] > 0]  # exclude zero-production entries (no bubble)

    if df.empty:
        raise ValueError(
            f"No valid data found for year {year} after filtering NaN and zero-production rows."
        )

    actual_year = int(
        ds_sel["cons"].sel(year=year, method="nearest").coords["year"].item()
    )
    period_label = "projected" if actual_year > base_year else "historical"

    # ------------------------------------------------------------------ #
    # Normalise bubble sizes                                               #
    # ------------------------------------------------------------------ #
    prod_values = df["prod"].values
    # Map production to marker area in points^2 — scale so the largest
    # bubble has area ~2000 pt^2 and the smallest at least ~20 pt^2.
    max_prod = prod_values.max()
    sizes = 20 + 1980 * (prod_values / max_prod)

    # ------------------------------------------------------------------ #
    # Colours                                                              #
    # ------------------------------------------------------------------ #
    if show_regions:
        # Assign one colour per region using the default colour cycle
        regions = df["country"].values
        unique_regions = list(dict.fromkeys(regions))  # preserve order, deduplicate
        color_cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]
        region_color_map = {
            r: color_cycle[i % len(color_cycle)] for i, r in enumerate(unique_regions)
        }
        colors = [region_color_map[r] for r in regions]
        legend_handles = [
            matplotlib.patches.Patch(color=region_color_map[r], label=r)
            for r in unique_regions
        ]
        color_legend_title = "Region"
    else:
        # Colour by net-trade sign: blue = net exporter, red = net importer
        if has_nettrade:
            net = df["nettrade"].fillna(0).values
            colors = ["steelblue" if v >= 0 else "tomato" for v in net]
        else:
            colors = ["steelblue"] * len(df)
        legend_handles = [
            matplotlib.patches.Patch(color="steelblue", label="Net exporter"),
            matplotlib.patches.Patch(color="tomato", label="Net importer"),
        ]
        color_legend_title = "Trade balance"

    # ------------------------------------------------------------------ #
    # Units — convert volume variables to million m3                      #
    # ------------------------------------------------------------------ #
    cons_unit = ds["cons"].attrs.get("unit", "1000 m3")
    prod_unit = ds["prod"].attrs.get("unit", "1000 m3")
    gdp_unit = ds["gdp"].attrs.get("unit", "USD")

    if cons_unit in ("1000 m3", "1000m3"):
        df["cons"] = to_million_m3(df["cons"])
        cons_unit = "million m3"
    if prod_unit in ("1000 m3", "1000m3"):
        df["prod"] = to_million_m3(df["prod"])
        prod_unit = "million m3"
        if has_nettrade and "nettrade" in df.columns:
            df["nettrade"] = to_million_m3(df["nettrade"])

    product_name = getattr(
        ds, "product", str(ds.attrs.get("product", "forest product"))
    )

    # ------------------------------------------------------------------ #
    # Figure                                                               #
    # ------------------------------------------------------------------ #
    fig, ax = plt.subplots(figsize=(10, 7))

    sc = ax.scatter(
        df["gdp"].values,
        df["cons"].values,
        s=sizes,
        c=colors,
        alpha=0.70,
        edgecolors="white",
        linewidths=0.5,
    )

    # ------------------------------------------------------------------ #
    # Annotations: top 15 by production                                    #
    # ------------------------------------------------------------------ #
    top15 = df.nlargest(15, "prod")
    for _, row in top15.iterrows():
        ax.annotate(
            row["country"],
            xy=(row["gdp"], row["cons"]),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=7,
            color="0.25",
            clip_on=True,
        )

    # ------------------------------------------------------------------ #
    # Size legend (proxy artists for three representative bubble sizes)    #
    # ------------------------------------------------------------------ #
    size_legend_values = np.array(
        [prod_values.min(), np.percentile(prod_values, 50), prod_values.max()]
    )
    size_legend_sizes = 20 + 1980 * (size_legend_values / max_prod)
    size_handles = [
        matplotlib.lines.Line2D(
            [],
            [],
            marker="o",
            linestyle="None",
            markersize=np.sqrt(s),  # markersize is diameter in points
            color="0.55",
            label=f"{v:,.0f} {prod_unit}",
        )
        for s, v in zip(size_legend_sizes, size_legend_values)
    ]

    # ------------------------------------------------------------------ #
    # Legends                                                              #
    # ------------------------------------------------------------------ #
    color_leg = ax.legend(
        handles=legend_handles,
        title=color_legend_title,
        loc="upper left",
        fontsize=8,
        title_fontsize=8,
        framealpha=0.8,
    )
    ax.add_artist(color_leg)

    ax.legend(
        handles=size_handles,
        title=f"Production ({prod_unit})",
        loc="lower right",
        fontsize=8,
        title_fontsize=8,
        framealpha=0.8,
        handletextpad=1.5,
        labelspacing=1.2,
    )

    # ------------------------------------------------------------------ #
    # Axis labels and title                                                #
    # ------------------------------------------------------------------ #
    ax.set_xlabel(f"GDP ({gdp_unit})", fontsize=10)
    ax.set_ylabel(f"Consumption ({cons_unit})", fontsize=10)

    entity_label = "regions" if show_regions else "countries"
    ax.set_title(
        f"{product_name.capitalize()} — consumption vs. GDP by {entity_label}"
        f"\n(size = production, {actual_year}, {period_label})",
        fontsize=11,
    )

    ax.set_xscale("log")
    ax.set_yscale("log")

    fig.tight_layout()
    return fig
