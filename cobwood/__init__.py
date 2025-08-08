#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# Introduction

This documentation describes the cobwood package to analyse global forest
products markets. The package is distributed on the python pacage index at
https://pypi.org/project/cobwood/. The source code is available at
https://bioeconomy.gitlab.io/cobwood/cobwood/

Key Features:

- **Panel Data Structure**: The package represents international forest products market
  data through 2 dimensional arrays with multiple years
  and countries, enabling time-series and cross-sectional analysis.

- **Data Handling with Xarray**: Utilizes Xarray datasets to efficiently manipulate
  multi-dimensional data structures. X array is tightly integrated with pandas.
  Conversion to and from pandas data frames is very straightforward. Xarray datasets are
  saved on disk using the NetCDF format. This format has the advantage of providing good
  metadata descriptors. NetCDF is a standard data format used in earth systems
  modelling, that will just help this model become a component of a greater modelling
  tool chain.


# Models

The goal of cobwood is to provide a readable and reusable data structure to implement many forest sector models.


## GFPMx

Currently, only the GFFPMx model is available. We will now illustrate how to prepare the input data for that model, and how to define a scenario. Not that many scenarios can be defined from the same input data, by changing some of the variables, such as the GDP projections. We will then explain how to run the model.

0. The input data can be downloaded from the website of the university of
  Wisconsin and converted to CSV files. You need to do this step only once and
  can ignore it later on. Convert data to CSV files inside the cobwood_data
  directory:

    >>> from cobwood.gfpmx_spreadsheet_to_csv import gfpmx_spreadsheet_to_csv
    >>> gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-base2021.xlsb")

1. In the cobwood_data directory, write the following configuration files and call it `scenario/base_2021.yaml`

```
input_dir: "gfpmx_base2021"
base_year: 2021
description: "Reproduce the GFPMX base 2021 scenario"
```

2. Load the input data into a [GFPMX](cobwood/gfpmx.html) model object.

    >>> from cobwood.gfpmx import GFPMX
    >>> gfpmxb2021 = GFPMX(scenario="base_2021", rerun=True)

3. Run the model.At each step compare with the reference model run inside the
Excel Sheet:

    >>> gfpmxb2021.run(compare=True, strict=False)

4. Explore the model output tables and make plots.

    >>> print(gfpmxb2021["sawn"])
    >>> print(gfpmxb2021["sawn"]["cons"])
    >>> gfpmxb2021.facet_plot_by_var("indround")

"""

# Build in modules
from pathlib import Path
import os

# Where is the data, default case #
data_dir = Path("~/repos/cobwood_data/")
data_dir = data_dir.expanduser()

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
