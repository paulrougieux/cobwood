---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.11.3
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


# Sawnwood Consumption

```python
swd_cons = gfpmx_data['SawnCons']
swd_cons.iloc[[1,-1]]  
```

## Join GDP, prices and consumption data

```python
gdp = gfpmx_data['GDP']
gdp.iloc[[1,-1]]
```

```python
swd_price = gfpmx_data['SawnPrice']
swd_price.iloc[[1,-1]]
```

```python
swd_cons = gfpmx_data['SawnCons']
swd_cons['test'] = 1
swd_cons
```

## Verify simulation results

The spreadsheet contains both historical and simulated data. Simulation results start after the base year. Cells up until the base year contain historical data. Cells in base_year + 1 use formulas in the spreadsheet. Before we can perform the calculation, we join the price and GDP sheets to the consumption sheet.

```python
swd_cons['value2'] = 
```

```python

```
