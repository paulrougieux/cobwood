---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.5
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

```python
from cobwood.gfpmx import GFPMX
from cobwood.gfpmx_plot import plot_da_by_region
from cobwood.gfpmx_plot import facet_plot_by_var

# Equations only required for debugging
from cobwood.gfpmx_equations import world_price_indround
from cobwood.gfpmx_equations import world_price
```

<!-- #region -->
# Introduction

The purpose of this notebook is to reproduce estimations from the GFPMX model, using the spreadsheet data available from https://buongiorno.russell.wisc.edu/gfpm/.



Before using this object, the Excel file needs to be exported to csv files with:

      >>> from cobwood.gfpmx_spreadsheet_to_csv import gfpmx_spreadsheet_to_csv
      >>> gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-8-6-2021.xlsx")

<!-- #endregion -->

## Load data


```python
gfpmxb2018 = GFPMX(data_dir="gfpmx_8_6_2021", base_year=2018)
gfpmxb2020 = GFPMX(data_dir="gfpmx_base2020", base_year=2020)
gfpmxb2021 = GFPMX(data_dir="gfpmx_base2021", base_year=2021)
```

# Run


```python
gfpmxb2021.run()
```

# Issues


## World price issue

To investigate ths issue I move up the chain of equations:

- World price of sawnwood
- World price of industrial roundwood
- World production of industrial roundwood

```python
gfpmxb2020.sawn.price.loc["WORLD"].plot()
```

```python
print(world_price(gfpmxb2020.sawn, gfpmxb2020.indround, 2020))
print(world_price(gfpmxb2020.sawn, gfpmxb2020.indround, 2021))
```

```python
world_price_indround(gfpmxb2020.indround, gfpmxb2020.other, 2021)
```

```python
print(gfpmxb2020.indround["prod"].loc["WORLD", 2020])
print(gfpmxb2020.indround["prod"].loc["WORLD", 2021])
```

```python
gfpmxb2020.indround["prod"].loc["WORLD"].plot()
```

```python
import xarray
# Put world data in one dataset
ds = xarray.Dataset()
ds["indroundprod"] = gfpmxb2020.indround["prod"].loc["WORLD"]
ds["sawnprice"] = gfpmxb2020.sawn.price.loc["WORLD"]
print(ds)
```

# Base year 2018


## Destat and plots

```python
for ds in [gfpmxb2018.indround, gfpmxb2018.sawn, gfpmxb2018.panel, gfpmxb2018.pulp, gfpmxb2018.paper, gfpmxb2020.fuel]:
    facet_plot_by_var(ds)
```

```python

```

# Base year 2021

## Destat and plots

```python
for ds in [gfpmxb2021.indround, gfpmxb2021.sawn, gfpmxb2021.panel, gfpmxb2021.pulp, gfpmxb2021.paper, gfpmxb2021.fuel]:
    facet_plot_by_var(ds)
```

```python
facet_plot_by_var(gfpmxb2021.other, ["area", "stock"], ylabel="Area in 1000ha and stock in million m3")

```

```python
variables = ["cons", "imp", "exp", "prod", "price"]
ds = gfpmxb2021.sawn
df = ds.loc[{"country": ~ds.c}][variables].to_dataframe()
df = df.reset_index().melt(id_vars=["country", "year"])
df.query("year==2023") 
```

## EU countries only

```python

```
