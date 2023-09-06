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
import seaborn
from cobwood.gfpmx import GFPMX
from cobwood.gfpmx_data import convert_to_2d_array
from cobwood.gfpmx_plot import plot_ds_by_davar
from cobwood.gfpmx_equations import compute_country_aggregates
from biotrade.faostat import faostat
```

# Introduction

The purpose of this notebook is to run the SSP2 and degrowth scenarios. 

- There will be 2 versions of the SSP2, one by Joseph Buongiorno and the one used in Bordisrky et al.



## Load data


```python
eu_countries = faostat.country_groups.eu_country_names

# TODO: load output of the model runs

```

```python
#######################
# Create GFTMX copies #
#######################
gfpmxb2021 = GFPMX(data_dir="gfpmx_base2021", base_year=2021)
# Create deep copies with different GDP scenario
# SSP2 - Bodirstky model
gfpmxpikbau = copy.deepcopy(gfpmxb2021)
# Degrowth model, PIK FAIR GDP scenario
gfpmxpikfair = copy.deepcopy(gfpmxb2021)
```

```python
# Load GDP data
gdp_comp = pandas.read_parquet(cobwood.data_dir / "pik" / "gdp_comp.parquet")

def get_gdp_wide(df:pandas.DataFrame, column_name:str, year_min:int=1995):
    """Transform the given GDP column into wide format for transformation into
    a 2 dimensional data array"""
    index = ["country", "year"]
    return (
        df[index + [column_name]]
        .loc[df["year"]>=year_min]
        .assign(year=lambda x: "value_" + x["year"].astype(str))
        .pivot(index="country", columns="year", values=column_name)
        .reset_index()
    )
pik_fair = get_gdp_wide(gdp_comp, "pik_fair_adjgfpm2021")
pik_bau = get_gdp_wide(gdp_comp, "pik_bau_adjgfpm2021")

# Assign new GDP values to the GFTMX objects, reindex them like the existing gdp array
# so that they get empty values for the country aggregatesgfpmxb2021
# Convert from million USD to 1000 USD
gfpmxpikbau.gdp = convert_to_2d_array(pik_bau).reindex_like(gfpmxb2021.gdp) * 1e3
gfpmxpikfair.gdp = convert_to_2d_array(pik_fair).reindex_like(gfpmxb2021.gdp) * 1e3


# Set values of 'Netherlands Antilles (former)', 'French Guyana',
# To the same as the existing GDP projections in GFPMX 2021
selected_countries = ['Netherlands Antilles (former)', 'French Guyana']
gfpmxpikbau.gdp.loc[selected_countries] = gfpmxb2021.gdp.loc[selected_countries]
gfpmxpikfair.gdp.loc[selected_countries] = gfpmxb2021.gdp.loc[selected_countries]

```

# Run


```python
gfpmxb2021.run()
```

```python
gfpmxpikfair.run()
```

```python
gfpmxpikbau.run()
```

## Recompute historical aggregates

```python
# Re-compute the aggregates for the historical period 
# There seems to be an issue in the GFPMX spreadsheet where some continents get inverted
for year in range(1995,2022):
    compute_country_aggregates(gfpmxb2021.indround, year)
    compute_country_aggregates(gfpmxpikbau.indround, year)
    compute_country_aggregates(gfpmxpikfair.indround, year)

    compute_country_aggregates(gfpmxb2021.fuel, year)
    compute_country_aggregates(gfpmxpikbau.fuel, year)
    compute_country_aggregates(gfpmxpikfair.fuel, year)

    compute_country_aggregates(gfpmxb2021.sawn, year)
    compute_country_aggregates(gfpmxpikbau.sawn, year)
    compute_country_aggregates(gfpmxpikfair.sawn, year)

    compute_country_aggregates(gfpmxb2021.panel, year)
    compute_country_aggregates(gfpmxpikbau.panel, year)
    compute_country_aggregates(gfpmxpikfair.panel, year)

    compute_country_aggregates(gfpmxb2021.paper, year)
    compute_country_aggregates(gfpmxpikbau.paper, year)
    compute_country_aggregates(gfpmxpikfair.paper, year)

    compute_country_aggregates(gfpmxb2021.pulp, year)
    compute_country_aggregates(gfpmxpikbau.pulp, year)
    compute_country_aggregates(gfpmxpikfair.pulp, year)
```

# Plot output


## GFPMX base 2021

```python
for ds in [gfpmxb2021.indround, gfpmxb2021.sawn, gfpmxb2021.panel, gfpmxb2021.pulp, gfpmxb2021.paper, gfpmxb2021.fuel]:
    plot_ds_by_davar(ds)
```

## Pik BAU

```python
for ds in [gfpmxpikbau.indround, gfpmxpikbau.sawn, gfpmxpikbau.panel, gfpmxpikbau.pulp, gfpmxpikbau.paper, gfpmxpikbau.fuel]:
    plot_ds_by_davar(ds)
```

### EU countries

```python
selector = gfpmxpikbau.indround["prod"]["country"].isin(faostat.country_groups.eu_country_names)
df = (gfpmxpikbau.indround["prod"]
      .loc[selector]
      .to_pandas()
      .reset_index()
      .melt(id_vars='country', var_name='year', value_name='prod')
     )

seaborn.relplot(data=df, kind="line", col="country", col_wrap=6, x='year', y='prod', facet_kws={'sharey': False})
```

## Pik FAIR


```python
for ds in [gfpmxpikfair.indround, gfpmxpikfair.sawn, gfpmxpikfair.panel, gfpmxpikfair.pulp, gfpmxpikfair.paper, gfpmxpikfair.fuel]:
    plot_ds_by_davar(ds)
```

### EU Countries

```python
selector = gfpmxpikfair.indround["prod"]["country"].isin(faostat.country_groups.eu_country_names)
df = (gfpmxpikfair.indround["prod"]
      .loc[selector]
      .to_pandas()
      .reset_index()
      .melt(id_vars='country', var_name='year', value_name='prod')
     )

seaborn.relplot(data=df, kind="line", col="country", col_wrap=6, x='year', y='prod', facet_kws={'sharey': False})
```

```python
gfpmxpikfair.indround["prod"].loc[{"country":"Austria"}].to_pandas()
```

# Issues


## France



### Pik bau

```python
for ds in [gfpmxpikbau.indround, gfpmxpikbau.fuel]:
    plot_ds_by_davar(ds, countries=["France", "Greece", "Germany"])
```

### Pik Fair

```python
for ds in [gfpmxpikfair.indround, gfpmxpikfair.fuel]:
    plot_ds_by_davar(ds, countries=["France", "Greece", "Germany"])
```

```python
def plot_ds_by_country(ds, countries):
    """Plot one facet per country"""
    ylabel = "Quantity in 1000 m3"
    da_vars = ["cons", "imp", "exp", "prod"]
    df = ds.loc[{"country": countries}][da_vars].to_dataframe()
    df = df.reset_index().melt(id_vars=["country", "year"])
    g = seaborn.relplot(
      data=df,
      x="year",
      y="value",
      col="country",
      hue="variable",
      kind="line",
      col_wrap=5,
      height=3,
      facet_kws={"sharey": False, "sharex": False},
    )
    g.set(ylim=(0, None))
    g.fig.supylabel(ylabel)
    g.fig.suptitle(ds.product)
    g.fig.subplots_adjust(left=0.09, top=0.85)
    return g

plot_ds_by_country(gfpmxpikfair.indround, ["France", "Germany", "Greece"])
```

```python
plot_ds_by_country(gfpmxpikfair.fuel, ["France", "Germany", "Greece"])
```

```python
gfpmxpikfair.fuel.cons_gdp_elasticity.loc[{"country":["Germany", "Italy", "France"]}]
```

```python
gfpmxpikbau.fuel.cons_gdp_elasticity.loc[{"country":["Germany", "Italy", "France"]}]
```

## Greece

```python

```

## Curve inversion issue

- Issue was fixed by recomputing aggregates.

```python
# Mapping tables between continents and countries
# gfpmxb2021.data.country_groups.query("region == 'EUROPE'")
```

```python
# gfpmxb2021.data.country_groups.query("region == 'SOUTH AMERICA'")
```

```python
plot_ds_by_davar(gfpmxpikbau.indround, "cons")
```

```python

```
