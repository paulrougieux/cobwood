# a!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

# User Guide

This documentation describes the cobwood package to analyse global forest
products markets. Cobwood helps analyse wood products markets from raw logs to
semi finished products such as sawnwood, paper and panels. If you're interested
in questions like: How much sawnwood does Italy consume? Or what are the
scenarios for global roundwood production by 2050?. This package provides the
tools and data to quickly retrieve historical data and scenarios to simulate
potential future developments. The package organizes decades of international
consumption, production and trade data. The examples below will guide you
through accessing and working with data and scenarios.


# Links

The package is distributed on the python pacage index at
https://pypi.org/project/cobwood/. The source code is available at
https://bioeconomy.gitlab.io/cobwood/cobwood/


# Panel Data Structure

The cobwood package represents international forest products market data
through 2 dimensional arrays with multiple years and countries, enabling
time-series and cross-sectional analysis.

Load a model to reproduce the examples below:

    from cobwood.gfpmx import GFPMX
    model = GFPMX(scenario="base_2021", rerun=False)

Starting with a simple example, the sawnwood consumption in Italy in 2020 is
accessible through the "sawn" product and the "cons" variable as follows:

    model["sawn"]["cons"].loc["Italy", 2070].item()

    # 5307.847275379434

The time series for all years in Italy is accessible as a data frame as
follows:

    model["sawn"]["cons"].loc["Italy"].to_dataframe()

    #      country         cons
    # year
    # 1995   Italy  8126.000000
    # 1996   Italy  7078.000000
    # 1997   Italy  8516.000000
    # 1998   Italy  8721.000000
    # 1999   Italy  9023.000000
    # ...      ...          ...
    # 2067   Italy  5306.695434
    # 2068   Italy  5307.084872
    # 2069   Italy  5307.472006
    # 2070   Italy  5307.847275
    # 2071   Italy          NaN

    # [77 rows x 2 columns]

Cobwood utilizes Xarray datasets to efficiently manipulate multi-dimensional
data structures. X array is tightly integrated with pandas. Conversion to and
from pandas data frames is very straightforward.

All consumption time series for all years and all countries are accessible as a
data frame as follows:

    model["sawn"]["cons"].to_dataframe()

    #                        cons
    # country year
    # Algeria 1995     680.700000
    #         1996     502.800000
    #         1997     665.400000
    #         1998     679.800000
    #         1999     790.000000
    # ...                     ...
    # EUROPE  2067  142264.389155
    #         2068  142785.668853
    #         2069  143311.938636
    #         2070  143842.325350
    #         2071            NaN

    # [14399 rows x 1 columns]

The main Variables are production (prod), consumption (cons), import (imp),
export (exp) and price.

    selected_variables = ["cons", "prod", "imp", "exp", "price"]
    model["sawn"][selected_variables].to_dataframe()


    #                        cons           prod           imp            exp       price
    # country year
    # Algeria 1995     680.700000      12.800000    667.900000       0.000000  443.903867
    #         1996     502.800000      12.800000    490.000000       0.000000  393.071157
    #         1997     665.400000      12.800000    652.600000       0.000000  351.963573
    #         1998     679.800000      12.800000    667.000000       0.000000  318.725131
    #         1999     790.000000      12.800000    777.200000       0.000000  278.379100
    # ...                     ...            ...           ...            ...         ...
    # EUROPE  2067  142264.389155  258834.056697  75813.799887  192348.078142         NaN
    #         2068  142785.668853  260826.261676  76316.972174  194320.290505         NaN
    #         2069  143311.938636  262853.904524  76826.128428  196328.918956         NaN
    #         2070  143842.325350  264914.071865  77340.716970  198371.372494         NaN
    #         2071            NaN            NaN           NaN            NaN         NaN

    # [14399 rows x 5 columns]



All variables are described in the following table:

| Variable                             | Description                                                 |
| ------------------------------------ | ----------------------------------------------------------- |
| cons                                 | Consumption                                                 |
| cons_price_elasticity                | Consumption elasticity with respect to price                |
| cons_products_elasticity             | Consumption elasticity with respect to other products       |
| cons_constant                        | Constant term in consumption equation                       |
| cons_usd                             | Consumption in USD                                          |
| exp                                  | Export                                                      |
| exp_marginal_propensity_to_export    | Marginal propensity to export                               |
| exp_constant                         | Constant term in export equation                            |
| exp_usd                              | Export in USD                                               |
| imp                                  | Import                                                      |
| imp_price_elasticity                 | Import elasticity with respect to price                     |
| imp_products_elasticity              | Import elasticity with respect to other products            |
| imp_constant                         | Constant term in import equation                            |
| imp_usd                              | Import in USD                                               |
| nettrade                             | Net trade                                                   |
| nettrade_usd                         | Net trade in USD                                            |
| price                                | Price                                                       |
| price_trend                          | Price trend                                                 |
| price_stock_elast                    | Price elasticity with respect to stock                      |
| price_world_price_elasticity         | Price elasticity with respect to world price                |
| price_constant                       | Constant term in price equation                             |
| prod                                 | Production                                                  |
| prod_usd                             | Production in USD                                           |
| tariff                               | Tariff                                                      |
| c                                    | Constant                                                    |
| cons_gdp_elasticity                  | Consumption elasticity with respect to GDP                  |
| conspercap                           | Consumption per capita                                      |
| imp_gdp_elasticity                   | Import elasticity with respect to GDP                       |
| price_input_elast                    | Price elasticity with respect to input                      |
| gdp                                  | Gross Domestic Product                                      |
| cons_paper_production_elasticity     | Consumption elasticity with respect to paper production     |
| imp_paper_production_elasticity      | Import elasticity with respect to paper production          |

To explore available variables, users can access the `variables` property (e.g.,
`model["sawn"].variables`).

Units are stored as Array properties are used to store metadata, the example
below displays the roundwood production unit :

```
model["indround"]["prod"].unit
# '1000m3'
```

After the model run, the output Xarray datasets are saved on disk using the
NetCDF format. This format has the advantage of providing good metadata
descriptors. NetCDF is a common data format used in earth systems modelling.
Display the path of the NetCDF file for the current model object:

    model.combined_netcdf_file_path

The products available are: industrial roundwood ('indround'), fuel wood
('fuel'), sawnwood ('sawn'), wood panels ('panel'), 'pulp' and  'paper'.

In summary:

- Forest products consumption, production, trade flows, and prices for all countries
 are stored as a Xarray datasets.

- Within each dataset for one product, specific variables are accessible as
  two-dimensional arrays with country and year coordinates (e.g.,
  `model["sawn"]["cons"]` for consumption)


# Models

Trees grow over decades or centuries and wood markets can be very localized.
Yet markets for processed wood and paper products are interconnected through
global trade networks. To simulate the future condition of wood markets, forest
economists rely on macroeconomic forest sector models. The goal of cobwood is
to provide a reusable data structure to implement many forest sector models.


## Model run

Forest sector models operate in static and dynamic phases. The static phase
balances supply and demand within a single year. The dynamic phase projects
future demand and supply driven by exogenous factors like GDP growth and
changes in the forest stock. Running a model means simulating the dynamic
phase through time.


## GFPMx

Currently, only the GFFPMx model is available. We will now illustrate how to
prepare the input data for that model, and how to define a scenario. Not that
many scenarios can be defined from the same input data, by changing some of the
variables, such as the GDP projections. We will then explain how to run the
model.

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
# package as well?
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
