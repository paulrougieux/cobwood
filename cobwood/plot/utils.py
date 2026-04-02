"""Utility functions for cobwood plot modules."""


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

        from cobwood.plot.utils import to_million_m3
        result = to_million_m3(5000)  # 5.0

    """
    return x / 1000
