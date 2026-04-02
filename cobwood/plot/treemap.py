"""Treemap visualisation for forest products market data."""

import xarray
import plotly.express as px
import plotly.graph_objects as go


# Human-readable labels for variables shown in titles and hover text
_VAR_LABELS = {
    "cons": "Consumption",
    "prod": "Production",
    "imp": "Import",
    "exp": "Export",
    "nettrade": "Net trade",
    "price": "Price",
    "conspercap": "Consumption per capita",
}


def treemap(
    ds: xarray.Dataset,
    var: str = "prod",
    year: int = 2021,
) -> go.Figure:
    """Draw a treemap of individual countries sized and coloured by a variable.

    The treemap uses a two-level hierarchy: World → country.  Only individual
    countries are shown (continent/region aggregates where ``ds.c == False``
    are excluded).  Countries with zero or NaN values are dropped so they do
    not appear as slivers or blank tiles.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset for a single forest product (e.g. ``gfpmxb2021["sawn"]``).
        Must contain a boolean coordinate ``c`` where ``True`` marks
        individual countries and ``False`` marks continents/regions, and a
        ``product`` attribute used in the plot title.
    var : str, optional
        Name of the variable to use for tile size and colour.
        Defaults to ``"prod"``.  A :class:`ValueError` is raised when the
        variable is absent from *ds*.
    year : int, optional
        The year slice to display.  Defaults to ``2021``.

    Returns
    -------
    plotly.graph_objects.Figure
        Interactive Plotly treemap figure.

    Raises
    ------
    ValueError
        If *var* is not available in *ds*.

    Example
    -------
    ::

        from cobwood.gfpmx import GFPMX
        from cobwood.plot import treemap
        gfpmxb2021 = GFPMX(scenario="base_2021", rerun=False)
        fig = treemap(gfpmxb2021["sawn"], var="prod", year=2021)
        fig.write_image(gfpmxb2021.plot_dir / "treemap.png")

    """
    # ------------------------------------------------------------------ #
    # Variable availability check                                          #
    # ------------------------------------------------------------------ #
    available = sorted(v for v in ds.variables if v not in ds.coords)
    if var not in ds.variables:
        raise ValueError(
            f"Variable '{var}' not found in dataset. "
            f"Available variables: {available}"
        )

    # ------------------------------------------------------------------ #
    # Select individual countries at the requested year                   #
    # ------------------------------------------------------------------ #
    ds_countries = ds.loc[{"country": ds.c}]
    da = ds_countries[var].sel(year=year, method="nearest")

    df = da.to_dataframe().reset_index()

    # Drop NaN and zero rows so treemap tiles are meaningful
    df = df.dropna(subset=[var])
    df = df[df[var] > 0]

    if df.empty:
        raise ValueError(
            f"No valid data found for variable '{var}' in year {year} "
            "after filtering NaN and zero-value rows."
        )

    # ------------------------------------------------------------------ #
    # Labels and title                                                     #
    # ------------------------------------------------------------------ #
    product_name = getattr(
        ds, "product", str(ds.attrs.get("product", "forest product"))
    )
    unit = ds[var].attrs.get("unit", "1000m3")
    actual_year = int(da.coords["year"].item())
    period_label = "projected" if actual_year > 2021 else "historical"

    var_label = _VAR_LABELS.get(var, var)
    colorbar_label = f"{var_label} ({unit})"
    title = (
        f"{product_name.capitalize()} — {var_label} by country"
        f" ({actual_year}, {period_label})"
    )

    # Add a constant root column so plotly can build World → country hierarchy
    df["World"] = "World"

    # ------------------------------------------------------------------ #
    # Build figure                                                         #
    # ------------------------------------------------------------------ #
    fig = px.treemap(
        df,
        path=["World", "country"],
        values=var,
        color=var,
        color_continuous_scale="YlOrRd",
        title=title,
        labels={var: colorbar_label},
        hover_data={var: ":.1f"},
    )

    fig.update_coloraxes(colorbar_title_text=colorbar_label)
    fig.update_traces(
        texttemplate="%{label}<br>%{value:,.0f}",
        hovertemplate=(
            "<b>%{label}</b><br>"
            + f"{var_label}: %{{value:,.1f}} {unit}"
            + "<extra></extra>"
        ),
    )
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))

    return fig
