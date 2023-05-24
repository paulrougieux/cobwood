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
from cobwood.gfpmx_data import gfpmx_data
import numpy as np
import pandas
```

# Introduction

The purpose of this document is to describe an implementation of the Global Forest
Products Trade Model in a cobweb form. It is inspired by Joseph Buongiorno's cobweb
GFPMX: "A Cobweb Model of the Global Forest Sector, with an Application to the Impact of
the COVID-19 Pandemic" https://doi.org/10.3390/su13105507. The GFPMX input data and
parameters are available as a spreadsheet at: https://buongiorno.russell.wisc.edu/gfpm/.

Goals:
1. Reproduce the GFPMX results using the same input data.
2. Update the input data from FAOSTAT and perform the computation.
3. Re-estimate the elasticities

# Data structure

The variables production $P$, import $I$, export $E$ and demand $D$ are distributed 
across commodity $c$, reporter $r$, and time $t$. In each country $r$, the variables are 
related through the following equation across all values of $c$, and $t$:

$$P_{crt} + I_{crt} - E_{crt} = D_{crt}$$ 


## Pandas, Numpy or Xarray

[Data Formats for Panel Data 
Analysis](https://bashtage.github.io/linearmodels/panel/examples/data-formats.html)

> There are two primary methods to express data:
> 
> - MultiIndex DataFrames where the outer index is the entity and the inner is the time 
>   index. This requires using pandas.
> 
> - 3D structures were dimension 0 (outer) is variable, dimension 1 is time index and 
>   dimension 2 is the entity index. It is also possible to use a 2D data structure with 
>   dimensions (t, n) which is treated as a 3D data structure having dimensions (1, t, n). 
>   These 3D data structures can be pandas, NumPy or xarray.

[Pandas for panel data](https://python.quantecon.org/pandas_panel.html)

Explains multi index with stacking and unstacking.

# Sample data from GFTMX

## Sawnwood

```python
swd_sheets = gfpmx_data.list_sheets().query("product=='sawn'")
known_columns = ['id', 'year', 'unnamed_2', 'constant', 'unnamed_1', 'faostat_name', 'country', 'value']
print("Additional variables besides the value in each sheet:")
for s in swd_sheets.name:
    print("  ", s, set(gfpmx_data[s].columns) - set(known_columns))
    #display(gfpmx_data[s].head(1))
```

```python
swd_cons = gfpmx_data['sawncons']
print(swd_cons.columns)
print(swd_cons.year.unique())
index = ["faostat_name", "country", "year"]
#index = ["country", "year"]
swd_cons = swd_cons.set_index(index)
swd_cons
```

```python tags=[]
#help(swd_cons.index)
```

```python
swd_cons.loc[("Sawnwood+sleepers", "Algeria", 1992)]
```

```python
swd_cons.loc[("Sawnwood+sleepers", "Algeria", 2017)]
```

##  Other products

```python
sheets = gfpmx_data.list_sheets()
for prod in sheets["product"].unique():
    sheets_selected = sheets.query("product==@prod")
    known_columns = ['id', 'year', 'unnamed_2', 'constant', 'unnamed_1', 'faostat_name', 'country', 'value']
    print(f"Additional variables in {prod}-related sheets:")
    for s in sheets_selected.name:
        print("  ", s, set(gfpmx_data[s].columns) - set(known_columns))
        #display(gfpmx_data[s].head(1))
```

# Other Variables

```python
sheets_selected = sheets.query("product!=product")
known_columns = ['id', 'year', 'unnamed_2', 'constant', 'unnamed_1', 'faostat_name', 'country', 'value']
print(f"Additional variables in {prod}-related sheets:")
for s in sheets_selected.name:
    print("  ", s, set(gfpmx_data[s].columns) - set(known_columns))
    #display(gfpmx_data[s].head(1))
```

# np.array test

```python
X_test= np.array([[0.33279229, 0.52539847, 0.32301045, 0.08504233],
[0.18115765, 0.11468587, 0.34419565, 0.91663379],
[0.55340608, 0.80923817, 0.24275124, 0.83075826],
[0.96856274, 0.43972433, 0.02564373, 0.51602777],
[0.5127286 , 0.88340132, 0.5584916 , 0.36889873],
[0.29306659, 0.82146901, 0.48855817, 0.93730368],
[0.9914627 , 0.81634472, 0.58954755, 0.9969822 ],
[0.3480635 , 0.59528288, 0.96056427, 0.41617849],
[0.88517647, 0.36977957, 0.69322023, 0.09770496],
[0.9115624 , 0.50818111, 0.94525091, 0.53483017],
[0.8379305 , 0.91641027, 0.03112315, 0.55125694],
[0.02452024, 0.72898607, 0.28460244, 0.34467602],
[0.17242202, 0.05892018, 0.19770165, 0.37108781],
[0.01634621, 0.93051447, 0.45819514, 0.71471246],
[0.84937553, 0.23620682, 0.60876167, 0.30354231]])
display(X_test)
X_test @ np.array(range(4))
```

```python
X = np.array([[0.33279229, 0.52539847, 0.32301045, 0.08504233],
              [0.18115765, 0.11468587, 0.34419565, 0.91663379],
              [0.55340608, 0.80923817, 0.24275124, 0.83075826],
              [0.96856274, 0.43972433, 0.02564373, 0.51602777]])


```

```python
# TODO: Check how to convert a data frame indexed column into a multi dimentional array
help(np.array)
```

```python

```

```python

```
