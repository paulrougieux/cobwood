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
import copy
import pandas
import cobwood
from cobwood.gfpmx import GFPMX
```

# Introduction

The purpose of this notebook is to run the SSP2 and degrowth scenarios. 

- There will be 2 versions of the SSP2, one by Joseph Buongiorno and the one used in Bordisrky et al.



## Load data


```python
gfpmxb2021 = GFPMX(data_dir="gfpmx_base2021", base_year=2021)
```

```python
# Load GDP data
gdp_comp = (
    pandas.read_parquet(cobwood.data_dir / "pik" / "gdp_comp.parquet")
)
```

```python
# Create a deep copy with different gdp scenario
# SSP2 - Bodirstky model
gfpmpikssp2 = copy.deepcopy(gfpmxb2021)
# Degrowth model, PIK FAIR GDP scenario
gfpmpikfair = copy.deepcopy(gfpmxb2021)
```

# Run


```python

```
