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
from cobwood.gfpmx_data import GFPMXData
from cobwood.gfpmx_plot import plot_da_by_region
from cobwood.gfpmx_plot import plot_ds_by_davar

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
gfpmxb2018 = GFPMXData(data_dir="gfpmx_8_6_2021", base_year=2018)
gfpmxb2020 = GFPMXData(data_dir="gfpmx_base2020", base_year=2020)
gfpmxb2021 = GFPMXData(data_dir="gfpmx_base2021", base_year=2021)
```

# Run


```python
# gfpmx_base_2018.run_and_compare_to_ref()
gfpmxb2020.run_and_compare_to_ref()
# gfpmx_base_2021.run_and_compare_to_ref()
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

# Destat and plots


## By continents

```python
plot_da_by_region(gfpmxb2020.indround, "prod")
```

```python
plot_da_by_region(gfpmxb2020.indround, "cons")
```

```python
plot_da_by_region(gfpmxb2020.indround, "imp")
```

```python
plot_da_by_region(gfpmxb2020.indround, "exp")
```

```python
gfpmxb2020.indround
```

```python

```

```python
import seaborn
indround = gfpmxb2020.indround.loc[{"country":~gfpmxb2020.indround.c}][["cons", "imp", "exp", "prod", "price"]].to_dataframe()
indround = indround.reset_index().melt(id_vars=["country", "year"])
indround
g = seaborn.relplot(
    data=indround, x="year", y="value", col="variable",
    hue="country", kind="line",
    col_wrap=5, height=3,
    facet_kws={'sharey': False, 'sharex': False}
)
g.fig.supylabel("Quantity in 1000 m3, price in USD/m3")
g.fig.subplots_adjust(left=0.28)
g.set(ylim=(0, None))
```

```python
type(g)
```

```python
plot_ds_by_davars(gfpmxb2020)
```

```python
plot_ds_by_davar(gfpmxb2020.indround)
```

```python
plot_ds_by_davar(gfpmxb2020.sawn)
```

```python

```
