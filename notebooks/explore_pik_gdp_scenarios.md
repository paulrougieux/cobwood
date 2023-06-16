```python
import pandas
import seaborn
import numpy as np
import matplotlib.pyplot as plt
import cobwood
from biotrade.faostat import faostat
```

# Introduction

The purpose of this notebook is to explore GDP scenarios from the paper:

- Bodirsky, B.L., Chen, D.MC., Weindl, I. et al. Integrating degrowth and efficiency
    perspectives enables an emission-neutral food system by 2100. Nat Food 3, 341–348
    (2022). https://doi.org/10.1038/s43016-022-00500-3

- The source data is located at: https://zenodo.org/record/5543427#.Y3eYOkjMKcM

- We compare those GDP series to the World bank historical GDP data and to GDP projections of the SSP2 scenario
  used in the GFPMx model.

- The data is prepared in a script which can be run at the command line with:

      ipython -i ~/repos/cobwood/scripts/load_pik_data.py






## Load data

```python
eu_countries = faostat.country_groups.eu_country_names
comp_eu = pandas.read_parquet(cobwood.data_dir / "pik" / "comp_eu.parquet")
gdp_comp = (
    pandas.read_parquet(cobwood.data_dir / "pik" / "gdp_comp.parquet")
)

# Reshape to long format
comp_eu_long = comp_eu.melt(
    id_vars=["country_iso", "year", "country"], var_name="source", value_name="gdp"
)
gdp_comp_long = gdp_comp.drop(columns=["pik_bau_i", "pik_fair_i"]).melt(
      id_vars=["country_iso", "year", "country", "continent"], var_name="source", value_name="gdp"
)
```

```python
comp_eu.columns
```

# Comparison plots


## XY comparison plots

```python
# Compare PIK BAU to GFTMx GDP scenario
comp_eu["country"] = comp_eu["country"].astype("category")
g = seaborn.FacetGrid(
    comp_eu.query("not pik_bau.isna()"),
    col="country",
    col_wrap=6,
    sharex=False,
    sharey=False,
)  # , height=6)
g.map_dataframe(seaborn.scatterplot, x="gfpm_gdp_b2018", y="pik_bau", hue="country")
# From https://stackoverflow.com/questions/54390054/how-to-add-a-comparison-line-to-all-plots-when-using-seaborns-facetgrid
def const_line(*args, **kwargs):
    x = np.arange(0, 1e7, 1e6)
    plt.plot(x, x)
g.map(const_line)
```

## X along time


## PIK GDP 2005 constant USD - Others GDP 2017 constant USD

```python
# GDP in billion USD
comp_eu_long["gdp_b"] = comp_eu_long["gdp"] / 1e3
g = seaborn.relplot(
    data=comp_eu_long,
    x="year",
    y="gdp_b",
    col="country",
    col_wrap=7,
    hue="source",
    style="source",
    kind="line",
    height=3,
    facet_kws={"sharey": False, "sharex": False},
)
g.fig.supylabel("GDP in billion USD")
g.fig.subplots_adjust(left=0.05)
g.set(ylim=(0, None))
# plt.savefig("/tmp/comp_gdp_by_country.pdf")
# plt.savefig("/tmp/comp_gdp_by_country.png")
```

```python
# Whole EU
comp_eu_long_agg = (
    comp_eu_long.groupby(["year", "source"])
    .agg(sum)
    .reset_index()
    # TODO: fix this in a more elegant way
    .query("gdp>0.1")
    .copy()
)

selected_sources = ["gfpm_gdp_b2018", "gfpm_gdp_b2021", "pik_bau", "pik_fair"]
p = seaborn.lineplot(
    x="year",
    y="gdp_b",
    hue="source",
    data=comp_eu_long_agg.query("source in @selected_sources"),
)
p.set(ylabel="GDP in billion USD", title="EU GDP scenarios")
plt.show()
# plt.savefig("/tmp/comp_gdp_eu_aggregate.png")
```

## GDP rescaled to 2017 or 2021 values

```python
gdp_comp_long["gdp"]
```

```python
# With rescaled values

gdp_comp_long["gdp_b"] = gdp_comp_long["gdp"] / 1e3
g = seaborn.relplot(
    data=gdp_comp_long.query("country in @eu_countries"),
    x="year",
    y="gdp_b",
    col="country",
    col_wrap=7,
    hue="source",
    style="source",
    kind="line",
    height=3,
    facet_kws={"sharey": False, "sharex": False},
)
g.fig.supylabel("GDP in billion USD")
g.fig.subplots_adjust(left=0.05)
g.set(ylim=(0, None))
#plt.savefig("/tmp/comp_gdp_by_country_rescaled.pdf")
# plt.savefig("/tmp/comp_gdp_by_country.png")
```

```python
# Whole EU
gdp_comp_long_agg_eu = (
    gdp_comp_long
    .query("country in @eu_countries")
    .groupby(["year", "source"])
    .agg(sum)
    .reset_index()
    # TODO: fix this in a more elegant way
    .query("gdp>0.1")
    .copy()
)

selected_sources = ["gfpm_gdp",
                    "pik_bau", "pik_fair",
                    "pik_bau_adjwb2017", "pik_fair_adjwb2017",
                    "pik_bau_adjgfpm2017", "pik_fair_adjgfpm2017",
                    "pik_bau_adjgfpm2021", "pik_fair_adjgfpm2021",
                    "wb_gdp_cst"]
p = seaborn.lineplot(
    x="year",
    y="gdp",
    hue="source",
    data=gdp_comp_long_agg_eu.query("source in @selected_sources"),
)
p.set(ylabel="GDP in billion USD", title="EU GDP scenarios")
plt.show()
# plt.savefig("/tmp/comp_gdp_eu_aggregate.png")
```

```python
gdp_comp_long_agg_eu.query("source in @selected_sources")
```

# Decrease profile in the degrowth scenario


## By continent

The plot by country and by continent below illustrate how African countries are
continuing to grow in the FAIR scenario, with the redistribution happening from high
income countries. Developed countries such as Canada, USA, Japan and European countries
see a decrease in GDP.


### Grouped

```python
#com_agg = (
#    gdp_comp_long
#    .groupby(["year", "continent"]
```

```python
this_continent = "Africa"
g = seaborn.relplot(
        data=gdp_comp.query("continent == @this_continent"),
        x="year",
        y="pik_fair_i",
        col="country",
        col_wrap=7,
        kind="line",
        height=3,
        facet_kws={"sharey": False, "sharex": False},
    )
g.fig.suptitle(f"PIK Fair GDP in {this_continent}")
g.fig.supylabel("GDP in billion USD")
g.fig.subplots_adjust(left=0.05)
g.set(ylim=(0, None))
plt.subplots_adjust(top=0.95)
plt.show()
```

### Each country detailed

```python
continents = list(gdp_comp["continent"].unique())
```

```python
for this_continent in continents:
    g = seaborn.relplot(
        data=gdp_comp.query("continent == @this_continent"),
        x="year",
        y="pik_fair_i",
        col="country",
        col_wrap=7,
        kind="line",
        height=3,
        facet_kws={"sharey": False, "sharex": False},
    )
    g.fig.suptitle(f"PIK Fair GDP in {this_continent}")
    g.fig.supylabel("GDP in billion USD")
    g.fig.subplots_adjust(left=0.05)
    g.set(ylim=(0, None))
    plt.subplots_adjust(top=0.95)
    plt.show()
```

```python
gdp_comp.columns
```

## Shift forward by 5 years

```python
gdp_comp
```

```python
# Shift by 5 years
gdp_comp["pik_fair_shift_5"] = gdp_comp.groupby("country_iso")["pik_fair_adjgfpm2017"].shift(periods=5)

# Whole EU
gdp_comp_long_agg_eu_2 = (
    gdp_comp
    .melt(id_vars=["country_iso", "year", "country", "continent"], var_name="source", value_name="gdp")
    .query("country in @eu_countries")
    .groupby(["year", "source"])
    .agg(sum)
    .reset_index()
    # TODO: fix this in a more elegant way
    .query("gdp>0.1")
    .copy()
)

selected_sources = ["gfpm_gdp_b2021", "pik_bau_adjgfpm2021", "pik_fair_adjgfpm2021", "pik_fair_shift_5"]
p = seaborn.lineplot(
    x="year",
    y="gdp",
    hue="source",
    data=gdp_comp_long_agg_eu_2.query("source in @selected_sources"),
)
p.set(ylabel="GDP in billion USD", title="EU GDP scenarios")
plt.show()
# plt.savefig("/tmp/comp_gdp_eu_aggregate.png")
```

```python
p = seaborn.lineplot(
    x="year",
    y="gdp",
    hue="source",
    data=gdp_comp_long_agg_eu_2.query("source in @selected_sources and year>=2020 and year<=2030"),
)
p.set(ylabel="GDP in billion USD", title="EU GDP scenarios (zoom 2020-2030)")
plt.show()
```

```python
# (
#         gdp_comp_long_agg_eu_2
#         .query("source in @cols_plot.keys()")
#         .assign(source = lambda x: x["source"].replace(cols_plot))
#     )
```

```python
selected_sources = ["", "pik_fair_adjgfpm2017"]
cols_plot = {
      "gfpm_gdp": "GFPMx SSP2 GDP",
      "pik_fair_adjgfpm2017": "PIK Fair GDP"
}
style_dict = {list(cols_plot.values())[0]: ('-', 'black'), list(cols_plot.values())[1]: ('--', 'black')}
df = (
        gdp_comp_long_agg_eu_2
        .query("source in @cols_plot.keys() and year <= 2050")
        .assign(gdp_bil = lambda x: x["gdp"] / 1e3,
                source = lambda x: x["source"].replace(cols_plot))
    )
p = seaborn.lineplot(
    x="year",
    y="gdp_bil",
    style="source",
    data=df
)
# Apply custom linestyle and color for each source
for line, source in zip(p.lines, df["source"].unique()):
    linestyle, color = style_dict[source]
    line.set_linestyle(linestyle)
    line.set_color(color)

p.set(ylabel="GDP in billion USD", title="EU GDP scenarios")
plt.show()
```

## EU GDP change over the period



```python
(gdp_comp_long_agg_eu_2
 .query("year in [2020,2050]")
 .pivot(index = "source", columns="year", values="gdp")
 .assign(change = lambda x: (x[2050] / x[2020] -1)*100)
)

```

```python
#for this_continent in continents:
this_continent == "Africa"
comp_africa = gdp_comp.query("continent == @this_continent")
```

```python
# Pivot wider and write to a csv file for use in the Excel version of the model

```

```python

```
