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


# Consumption


## Sanwood consumption

```python
swd_cons = gfpmx_data['SawnCons']
swd_cons.iloc[[1,-1]]  
```

### Verify results


```python
swd_cons.columns
```

```python

```
