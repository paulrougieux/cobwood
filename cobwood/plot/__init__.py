"""Plot functions for cobwood forest products market analysis."""
from cobwood.plot.choropleth import choropleth_map
from cobwood.plot.sparklines import sparklines
from cobwood.plot.stacked_area import stacked_area
from cobwood.plot.scatter_matrix import scatter_matrix
from cobwood.plot.bubble_chart import bubble_chart
from cobwood.plot.parallel_coordinates import parallel_coordinates
from cobwood.plot.grouped_bar import grouped_bar
from cobwood.plot.treemap import treemap
from cobwood.plot.trade_balance import trade_balance_matrix


def to_million_m3(x):
    """Convert values from 1000 m³ to million m³.

    Parameters
    ----------
    x : numeric or array-like
        Values expressed in 1000 m³.

    Returns
    -------
    numeric or array-like
        Values divided by 1000, expressed in million m³.

    Example
    -------
    ::

        from cobwood.plot import to_million_m3
        result = to_million_m3(5000)  # 5.0

    """
    return x / 1000


__all__ = [
    "to_million_m3",
    "choropleth_map",
    "sparklines",
    "stacked_area",
    "scatter_matrix",
    "bubble_chart",
    "parallel_coordinates",
    "grouped_bar",
    "treemap",
    "trade_balance_matrix",
]
