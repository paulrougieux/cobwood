"""Choropleth map visualisation for forest products market data."""

import xarray
import plotly.express as px
import plotly.graph_objects as go


def choropleth_map(
    ds: xarray.Dataset,
    var: str = "conspercap",
    year: int = 2021,
) -> go.Figure:
    """Draw a choropleth map of a single variable for individual countries.

    Only individual countries are shown (continent/region aggregates are
    excluded).  The country dimension must use names that Plotly can resolve
    via ``locationmode="country names"``.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset for a single forest product (e.g. ``gfpmxb2021["sawn"]``).
        Must contain a boolean coordinate ``c`` where ``True`` marks
        individual countries and ``False`` marks continents/regions, and a
        ``product`` attribute used in the plot title.
    var : str, optional
        Name of the variable to map.  Defaults to ``"conspercap"``.  If the
        variable is not present in *ds* a :class:`ValueError` is raised and
        the available variable names are listed.  When ``var="conspercap"``
        and that variable is absent, ``"cons"`` is used as a fallback without
        raising an error.
    year : int, optional
        The year slice to display.  Defaults to ``2021``.

    Returns
    -------
    plotly.graph_objects.Figure
        Interactive Plotly choropleth figure.

    Raises
    ------
    ValueError
        If *var* is not available in *ds* (and the ``conspercap`` fallback
        logic does not apply).

    Example
    -------
    ::

        from cobwood.gfpmx import GFPMX
        from cobwood.plot import choropleth_map
        gfpmxb2021 = GFPMX(scenario="base_2021", rerun=False)
        fig = choropleth_map(gfpmxb2021["sawn"], var="conspercap", year=2021)
        fig.write_image(gfpmxb2021.plot_dir / "choropleth.png")

    """
    # ------------------------------------------------------------------ #
    # Variable resolution with fallback                                    #
    # ------------------------------------------------------------------ #
    available = [v for v in ds.variables if v not in ds.coords]

    if var not in ds.variables:
        if var == "conspercap" and "cons" in ds.variables:
            var = "cons"
        else:
            raise ValueError(
                f"Variable '{var}' not found in dataset. "
                f"Available variables: {sorted(available)}"
            )

    # ------------------------------------------------------------------ #
    # Select individual countries at the requested year                   #
    # ------------------------------------------------------------------ #
    ds_countries = ds.loc[{"country": ds.c}]
    da = ds_countries[var].sel(year=year, method="nearest")

    df = da.to_dataframe().reset_index()
    # Drop NaN rows so Plotly does not render blank patches
    df = df.dropna(subset=[var])

    # ------------------------------------------------------------------ #
    # Labels                                                               #
    # ------------------------------------------------------------------ #
    product_name = getattr(
        ds, "product", str(ds.attrs.get("product", "forest product"))
    )
    unit = ds[var].attrs.get("unit", "")
    actual_year = int(da.coords["year"].item())
    period_label = "projected" if actual_year > 2021 else "historical"

    var_labels = {
        "conspercap": "Consumption per capita",
        "cons": "Consumption",
        "prod": "Production",
        "imp": "Import",
        "exp": "Export",
        "price": "Price",
        "nettrade": "Net trade",
        "gdp": "GDP",
    }
    var_label = var_labels.get(var, var)

    colorbar_label = f"{var_label}" + (f" ({unit})" if unit else "")
    title = (
        f"{product_name.capitalize()} — {var_label} by country"
        f" ({actual_year}, {period_label})"
    )

    # ------------------------------------------------------------------ #
    # Build figure                                                         #
    # ------------------------------------------------------------------ #
    fig = px.choropleth(
        df,
        locations="country",
        locationmode="country names",
        color=var,
        color_continuous_scale="YlOrRd",
        title=title,
        labels={var: colorbar_label},
    )

    fig.update_coloraxes(colorbar_title_text=colorbar_label)
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth"),
        margin=dict(l=0, r=0, t=50, b=0),
    )

    return fig
