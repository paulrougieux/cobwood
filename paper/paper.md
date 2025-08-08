---
title: "Cobwood: Enhancing Forest Economics Model Reusability Through labelled Panel Data Structures"
tags:
  - forest
  - macroeconomics
  - python
authors:
  - name: Paul Rougieux
    orcid: 0000-0001-9073-9826
    affiliation: "1"
    corresponding: true
affiliations:
 - name: European Commission, Joint Research Centre, Ispra, Italy
   index: 1
date: 2025
bibliography: paper.bib
---

<!--
The following comments will not appear in the paper.

- Journal of Open Source Software (JOSS)- Paper submission guidelines
  https://joss.readthedocs.io/en/latest/submitting.html

- Compile this paper to a pdf document with the script specified in .gitlab-ci.yml. JOSS
  uses the openjournals/inara docker image and compiles the document with the following
script:

        inara -p -o pdf paper/paper.md

- Extract documentation from the package docstrings with pdoc

        pdoc -o public ./cobwood/

- TODO: install the package in a new environment, based on the TOML file

End comments.
-->

# Summary

Managing forest ecosystems effectively requires long-term foresight into global wood
markets. This planning relies on macroeconomic panel data spanning multiple countries
over extended time periods. The cobwood package introduces a data structure for forest
sector forecasting and scenario analysis. Our data structure leverages labelled
N-dimensional arrays from the Xarray package, including output storage to NetCDF files.
This approach offers two key advantages: enhanced source code clarity that facilitates
model inspection, and comprehensive metadata for country, product, and time coordinates
along with units in the dataset attributes. To demonstrate cobwood's practical
application, we present a reimplementation of the Global Forest Products Model (GFPMx).
This standard data structure positions cobwood as an ideal component for
integration into modelling tool chains.


# Statement of need

Forest management requires a long-term perspective, as trees grow over decades or
centuries, while wood markets operate on a global scale. Decision makers in the forestry
sector need long-term forecasts of global wood consumption, production and trade
patterns. This need has prompted forest economists to develop macroeconomic models of
the forest sector. Several global forest sector models currently exist, including the
Global Forest Products Model (GFPM)[@buongiorno2003global], the European Forest
Institute Global Trade Model (EFI-GTM)[@kallio2004global], the Global Forest and
Agriculture Model (G4M)[@gusti2020g4m], the Global Forest Trade Model (GFTM)
[@jonsson2015global] and an adaptation called Timba [@tifsm2025]. There are also
numerous regional and national forest sector models.



Adjacent fields of research such as forestry, vegetation dynamic modelling or Life Cycle
Analysis need estimes of future processed wood consumption and future roundwood harvest.
The transparency of the models and algorithms are helpful when determining whether a
particular model is suitable for analysing specific policy questions or can be
appropriately modified for new purposes. While research papers describe the conceptual
specifications for these models, reading the source code of the model implementation
offers a more comprehensive understanding of the system.

Macroeconomic models typically organize market datasets along two dimensions: country
and time. In econometrics, the structure is known as panel data. Forest products market
datasets contain information on production, consumption, and trade for specific products
such as roundwood, sawnwood, wood panels, pulp, and paper products. Current
modelling software often lacks a panel data structure.
Instead, these programs use partial labelling approaches—such as matrices names or
vector names within data frames, or simple column names in spreadsheets. While this
approach can make programs more concise, it creates challenges for newcomers trying to
understand the models. Variable names are often unclear, making the code difficult to
interpret for those unfamiliar with the model's implementation. In addition, the limited
data labelling makes it harder to reuse the output data of those models. Examples of
readability issue can be found in the source code of models like GFTM, GFPM, and Timba.
That source code for other forest sector models, such as EFI-GTM and G4M-GLOBIOM-Forest,
is not yet publicly available for review.

The cobwood model has been used to produce scenario analysis for technical reports
@mubareka2025 and @rougieux2024. The first model programmed inside cobwood is a
reimplementation of a simple forest sector model, the main value of this python package
doesn't lie in the model itself, but in the panel data structure that can be used to
implement many models.

The next sections describe input output data and the data structure.


# Input, output

Cobwood can process **input** data from any tabular source that Python supports. For
instance, the GFPMx model uses a single Excel spreadsheet containing separate sheets for
consumption, production, import, export, and prices of major forest products from
FAOSTAT. The implementation first converts these sheets to CSV files, which the
gfpmx_data.py module then transforms into an Xarray data structure. Remember that Xarray
datasets can be converted to pandas data frame very easily.

**Output** data is saved in NetCDF format, which serves as Xarray's disk representation.
While not commonly used in economics, this format is standard in earth systems modelling,
making it ideal for integrated modelling systems where economic and biophysical models
exchange data. The `write_datasets_to_netcdf` method adds a third dimension coordinate
called "product" before saving datasets to NetCDF files. These files include metadata
labels for units, establishing a foundation for reproducible analysis across research
teams.

![Data structure](fig/data_structure_2.pdf "Structure of the
data"){#fig:structure}

# Data structure and implementation

Cobwood leverages Xarray's labelled data arrays to represent panel data, enabling a more
intuitive approach to economic modelling. This design allows developers to write Python
functions that closely mirror the mathematical equations found in academic literature,
with explicit time and country dimensions. The package is designed for extensibility
across different models, though the initial release focuses on implementing the Global
Forest Products Model (GFPMx) [@buongiorno2021gfpmx]. The core of cobwood is the GFPMX
object, which organizes global forest product data including consumption, production,
trade flows, and prices.

Data organization follows a logical hierarchy:

- Each forest product is stored as a separate Xarray dataset (e.g., gfpmx["sawn"] for
  sawnwood)
- Within each product dataset, specific variables are accessible as two-dimensional
  arrays (e.g., gfpmx["sawn"]["cons"] for consumption)
- These arrays maintain panel data structure with clear country and year dimensions
- Some variables, like demand elasticities, use only the country dimension

To explore available variables and their units for any product, users can access the
`variables` property (e.g., `gfpmxb2021["sawn"].variables`). For example this prints the
unit used by the roundwood product for the production variable:

```
gfpmxb2021["indround"]["prod"].unit
# '1000m3'
```

A key advantage of Xarray's approach is the automatic dimension alignment when
performing operations between arrays, which simplifies mathematical operations across
different data elements. As Figure \ref{fig:structure} illustrates, the labelled
panel data structure
creates a clean, organized data representation that makes the modelling system more
accessible to new users.


# Model run

Load the input data into a GFPMX model object. The `rerun=True` argument gives the
instruction to erase previous model runs of this scenario. When running the model,
`compare=True` argument makes it compare the model output with a reference model run
from the external model that we use as a reference in this case the Excel implementation
of GFPMx:

    from cobwood.gfpmx import GFPMX
    gfpmxb2021 = GFPMX(scenario="base_2021", rerun=True)
    gfpmxb2021.run(compare=True, strict=False)

After a model run, the scenario output data is automatically saved inside the model's
`output_dir` directory. When re-loading the model later, specify the argument
`rerun="False"` (default) to load both input and output data without the need to run the
model.


# Visualisation

The following python code draws a faceted plot of industrial roundwood
consumption, import, export, production and price. We don't need to re-run the model
this time since we can simply reload the model's output data from the previous run
above.

```
from cobwood.gfpmx import GFPMX
gfpmxb2021 = GFPMX(scenario="base_2021", rerun=False)
```

The first plot draws coloured lines by continents. It is the default plot.

```
gfpmxb2021.facet_plot_by_var("indround")
```

![Industrial roundwood variables by continent](fig/indround_by_continent.png "Plot of
industrial roundwood variables by
continent")

The country argument can specify one coloured line by country:

    gfpmxb2021.facet_plot_by_var("indround", countries=["Canada", "France", "Japan"])

![Industrial roundwood variables by country](fig/indround_by_country.png "Plot of
industrial roundwood variables by
country")


# Conclusion

The cobwood package introduces a new way to represent macroeconomic forest products
market data using N-dimensional labelled data arrays. This data structure, built on
Xarray, improves source code readability by allowing equations with time and country
coordinates to be easily identified in the code. Units are stored as metadata attributes
within the data structure. Model outputs are saved to NetCDF files, which preserve
Xarray’s data model, including dimensions and attributes. We believe this new structure
makes Cobwood an excellent foundation for implementing various forest sector models.
Additionally, the scenario configuration file enables easy comparison of multiple model
implementations across a wide range of configuration parameters.


# References


<!-- Save plots as images to be inserted in the paper

    from cobwood import data_dir
    from cobwood.gfpmx_equations import compute_country_aggregates
    plot_dir = data_dir.parent / "cobwood/paper/fig"
    gfpmxb2021 = GFPMX(
        input_dir="gfpmx_base2021", base_year=2021, scenario="base_2021",
        rerun=False
    )
    print("Re-compute aggregates for the historical period.")
    for this_product in gfpmxb2021.products:
        for year in range(1995, 2022):
            compute_country_aggregates(gfpmxb2021[this_product], year)
            compute_country_aggregates(gfpmxb2021.other, year, ["area", "stock"])

    # Draw the default plot with one line by continent
    g = gfpmxb2021.facet_plot("indround")
    g.savefig(plot_dir / "indround_by_continent.png")

    # Use the countries argument to specify one line by country
    g = gfpmxb2021.facet_plot("indround", countries=["Canada", "France", "Japan"])
    g.savefig(plot_dir / "indround_by_country.png")

Maybe use https://docs.xarray.dev/en/latest/generated/xarray.plot.pcolormesh.html

-->

