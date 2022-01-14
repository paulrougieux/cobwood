---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.13.4
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

```python
# Load 
from gftmx.gfpmx_data import gfpmx_data
```

# Introduction

The purpose of this notebook is to reproduce estimations from the GFPMX model, using the spreadsheet data available from https://buongiorno.russell.wisc.edu/gfpm/.


# Sawnwood 

```python
swd_cons = gfpmx_data['sawncons']
swd_cons.iloc[[1,-1]]  
```

## Join Consumption, GDP and price data

```python
gfpmx_data['gdp'].iloc[[1,-1]]
```

```python
gfpmx_data['sawnprice'].iloc[[1,-1]]
```

```python
index = ['id', 'year','country']
swd_cons = gfpmx_data['sawncons']
swd_cons = (swd_cons
            .merge(gfpmx_data.get_gdp(), 'left', index)
            .merge(gfpmx_data.get_price_lag('sawnprice'), 'left', index)
           )
swd_cons.drop(columns = ['faostat_name', 'price'], inplace=True)

# Compute the consumption equation
swd_cons['value2'] = swd_cons.constant * swd_cons['price_lag'].pow(swd_cons.price_elasticity) * \
    swd_cons.gdp.pow(swd_cons.gdp_elasticity)

swd_cons['comp_prop'] = swd_cons.value2 / swd_cons.value -1
# Don't display rows with NA values
display(swd_cons.query("price_lag==price_lag & gdp_elasticity==gdp_elasticity"))
```

## Verify simulation results

The spreadsheet contains both historical and simulated data. Simulation results start after the base year. Cells up until the base year contain historical data. Cells in base_year + 1 use formulas in the spreadsheet. Before we can perform the calculation, we join the price and GDP sheets to the consumption sheet.


### After the base year

Show the comparison proportion after the base year.

```python
# After the base year
swd_cons2 = swd_cons.query("year > @gfpmx_data.base_year & price_lag==price_lag & gdp_elasticity==gdp_elasticity")
swd_cons2
```

```python
swd_cons2.comp_prop.describe()
```

```python

```

```python

```
