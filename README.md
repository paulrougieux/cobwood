Cobwood is a Python package designed to analyse global forest products markets.

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


# Documentation

- The package documentation (generated from function and method docstrings) is available
  at https://bioeconomy.gitlab.io/cobwood/cobwood/cobwood.html

- Instructions below explain how to install and run the model.  They provide an
  overview of
  model
  formulation and data structure.

- The paper at paper describes the context and purpose of cobwood.


# Installation

Install from the python package index:

    pip install cobwood

Clone the cobwood_data to create the cobwood_data structure at the default location,
alternatively clone it at any location and set the environment variable `COBWOOD_DATA` to
define the location of the data:

    mkdir -p ~/repos
    cd ~/repos
    git clone git@gitlab.com:bioeconomy/cobwood/cobwood_data.git


## Optional virtual environment

Optionally create a virtual environment and install the `cobwood` package and
its dependencies inside this virtual environment:

    mkdir -p /tmp/cobwoodenv
    cd /tmp/cobwoodenv/
    python3 -m venv /tmp/cobwoodenv/
    source /tmp/cobwoodenv/bin/activate
    pip install cobwood

You can later on use the model inside this virtual environment by activating it each
time with:

    source /tmp/cobwoodenv/bin/activate


# Run the model

Currently, only the GFFPMx model is available. We will now illustrate how to initiate a
model instance for a given scenario. Scenarios are defined in the scenario input
directory
[cobwood_data/scenarios](https://gitlab.com/bioeconomy/cobwood/cobwood_data/-/tree/main/scenario?ref_type=heads)
as yaml files. They define variations of the model input, by changing some of the
variables, such as the GDP projections for example. Here is how to run the model to
reproduce a baseline scenario:

1. Load the input data into a
   [GFPMX](https://bioeconomy.gitlab.io/cobwood/cobwood/cobwood/gfpmx.html#GFPMX) model
   object.

```python
from cobwood.gfpmx import GFPMX
gfpmxb2021 = GFPMX(scenario="base_2021", rerun=True)
```

2. Run the model.At each step compare with the reference model run inside the Excel
   Sheet:

```python
gfpmxb2021.run(compare=True, strict=False)
```

3. Explore the model output tables and make plots.

```python
print(gfpmxb2021["sawn"])
print(gfpmxb2021["sawn"]["cons"])
gfpmxb2021.facet_plot_by_var("indround")
```


# Model Formulation

The core implementation serves as a foundation for developing various versions of global
forest sector models. A panel data structure based on N dimensional arrays  enable users
to extend, or customize the model to fit specific research questions.

The first model formulation is based on GFPMX: "A Cobweb Model of the Global Forest
Sector, with an Application to the Impact of the COVID-19 Pandemic" by Joseph Buongiorno
https://doi.org/10.3390/su13105507

The GFPMX input data and parameters are available as a spreadsheet at:
https://buongiorno.russell.wisc.edu/gfpm/


## Equations

Equations are defined using Xarray time and country indexes so that they appear similar
to mathematical equations used in the papers describing the model. For example, the
consumption equation in `cobwood/gfpmx_equations.py` takes a dataset and a specific time
`t` as input and returns a data array as output. The input dataset `ds` contains price
and GDP data for all time steps and all countries, as well as price and GDP
elasticities. The computation at a given time and for a given set of countries is done
by using the time index `t` and the country index  `ds.c` (which represents all
countries in the dataset) as follows:

    def consumption(ds: xarray.Dataset, t: int) -> xarray.DataArray:
        """Compute consumption equation 1"""
        return (
            ds["cons_constant"]
            * pow(ds["price"].loc[ds.c, t - 1], ds["cons_price_elasticity"])
            * pow(ds["gdp"].loc[ds.c, t], ds["cons_gdp_elasticity"])
        )



# Input data

The data is based on the FAOSTAT forestry production and trade data set available at:
http://www.fao.org/faostat/en/#data/FO/visualize


# Data structure

Cobwood implements simulations of the Global Forest Products Market (GFPM), covering
data for 180 countries over 80 years. Each equation within the model is structured over
two-dimensional Xarray data arrays, where:

- Countries form the first dimension (or coordinate), allowing for cross-sectional
  analysis.
- Years constitute the second dimension, facilitating time-series insights.

![Data structure](https://gitlab.com/bioeconomy/cobwood/cobwood/-/raw/main/paper/fig/data_structure_2.png)

**Data Manipulation and Export**. Xarray data arrays can be converted to a format
similar to the original GFPMx spreadsheet with countries in rows and years in columns.
For example the following code uses `DataArray.to_pandas()` to convert the pulp import
array to a csv file using the pandas to_csv() method:

    from cobwood.gfpmx_data import GFPMXData
    gfpmx_data = GFPMXData(data_dir="gfpmx_8_6_2021", base_year = 2018)
    pulp = gfpmx_data.convert_sheets_to_dataset("pulp")
    pulp["imp"].to_pandas().to_csv("/tmp/pulp_imp.csv")

Example table containing the first few lines and columns:

| country | 2019 | 2020 | 2021 |
|---------|------|------|------|
| Algeria | 66   | 61   | 56   |
| Angola  | 0    | 0    | 0    |
| Benin   | 0    | 0    | 0    |

The `DataArray.to_dataframe()` method converts an array and its coordinates into a long
format also called a tidy format with one observation per row.

    pulp["imp"].to_dataframe().to_csv("/tmp/pulp_imp_long.csv")

Example table containing the first few lines and columns:

| country | year | imp |
|---------|------|-----|
| Algeria | 2019 | 66  |
| Algeria | 2020 | 61  |
| Algeria | 2021 | 56  |

