#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Location of the data
"""

# Build in modules
from pathlib import Path
import os

# Where is the data, default case #
data_dir = Path("~/repos/cobwood_data/")
# TODO: remove when it is replaced everywhere by cobwood.data_dir. Maybe it's
# better to keep it that way explicitly in case we import data_dir from another
# package?
cobwood_data_dir = data_dir

# But you can override that with an environment variable #
if os.environ.get("COBWOOD_DATA"):
    data_dir = Path(os.environ["COBWOOD_DATA"])


def create_data_dir(path: str):
    """Create a sub directory of `data_dir`

    Example:

        >>> import cobwood
        >>> test_sub_dir = cobwood.create_data_dir("test")
        >>> print(test_sub_dir)

    """
    sub_dir = data_dir / path
    if not sub_dir.exists():
        sub_dir.mkdir()
    return sub_dir
