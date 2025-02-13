---
title: 'Cobwood: a multi dimensional data structure to analyse forest products markets with python'
tags:
  - python
  - life cycle analysis
  - forest
  - agriculture
  - land footprint
authors:
  - name: Paul Rougieux
    orcid: 0000-0001-9073-9826
    affiliation: "1"
    corresponding: true
  - name: Selene Patani
    orcid: 0000-0001-8601-3336
    affiliation: "2"
  - name: Sarah Mubareka
    orcid: 0000-0001-9504-4409
    affiliation: "1"
affiliations:
 - name: European Commission, Joint Research Centre, Ispra, Italy
   index: 1
 - name: JRC Consultant, ARCADIA SIT s.r.l., Vigevano (PV), Italy
   index: 2
date:
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

Managing forest ecosystem requires long term foresight of global wood markets. The
underlying market data for all world countries and along many years is called
macroeconomic panel data. The cobwood package proposes a data structure that facilitates
the manipulation of panel data for forecasts and scenario analysis. The uses of country
and time indexes enhances model readability because source code becomes similar to
modelling equations used to describe the model in research papers. We illustrate the
implementation of one forest sector model by reimplementing the cobwood version of the
Global Forest Products Model (GFPMx). Cobwood represents panel data by using the N
dimensional array package Xarray, which also includes the capability to save modelling
output to NetCDF files. The enhanced readability will make it easier to inspect the
source code of the model. The metadata on country, product, time dimensions and on units
present in output files makes cobwood a better candidate to become the component of a
greater modelling tool chain.


# Statement of need

Trees grow over many decades or centuries, and wood demand is globalized. To manage
forest ecosystems, decision makers need long term forecasts of the global consumption
and trade in forest products. They want to envision what could be potential future wood
harvest developments according to different scenarios on the demand side as well as on
the supply side of the markets. This is why forest economists have developed
macroeconomic models of the forest sector.

The following forest sector models are available at the global level: the Global Forest
Products Model (GFPM), the EFI-GTM (European Forest Institute Global Trade Model), the
G4M, The Global Forest Trade Model (GFTM). There is also a variant of the GFPM called
Timba. There are also many other forest sector models at the regional or national level.

Model transparency is important to understand whether a model is fit to analyse a policy
question, or whether it can be extended or modified for that purpose. Of course one
should start with the research papers that go along with a model, but reading the source
code leads to a much deeper understanding of the modelling system and it is necessary if
one plans on extending a model to analyse new research questions.


# Representation of panel data in other models

The cobwood package emphasises model readability through data labelling. Inside
macroeconomic forest sector models, market datasets are Generally structured with a
country and a time dimension, this data structure is called **panel data** in
econometrics. By market dataset we intent data on production, consumption and trade of a
specific product such as roundwood, sawnwood, wood pannels, pulp and paper products.
Typical representations of market data in modelling software lack a consistent labelled
panel data structure, instead, they have partial data labelling of matrices or vectors
inside data frames in the modelling language or column names in a spreadsheet. While
this can make some of these programs nicely concise, the obscurity of variable names and
the lack of data labelling makes them harder to read for the uninitiated. See for
example the source code of G4M, the Matlab source code of the GFTM, the source code of
GFPM, or the source code of Timba. The different models have various degrees of
readability which can be illustrated by looking at the way the macroeconmic demand for
wood products is implemented.

Figure illustrating the following points

- 2D panel data  countries x time
- 1D vector data elasticities
- Arrow to the gfpmx_data model object which contains data only
- Arrow to the gomx model object which contains the data and a modelling implementation
  in the form of equations.
- illustration of the gfpmx["sawn"] dataset containing many data arrays
- illustration of gfpmx["sawn"]["cons"] 2 dimensional data array



# Representation of panel data with Xarray

We have used the labelled data arrays from Xarray to represent panel data. This gives us
the possibility to use the time and countries dimensions to write python functions that
look similar to the equations describing a model.

On the output side, the data structure can be saved as NetCDF files, with added metadata
labels on units. This provides a solid ground for reproducibility of analysis by other
researchers teams.

The cobwood package is extensible and is meant to be used to represent different models,
but the first version only implements one model: the Global Forest Products Model called
GFPMx [@buongiorno2021gfpmx]. The cobwood package contains a `GFPMX` object that
represents global forest products consumption, production, import, export and prices of
forest products. Each product is represented as a separate Xarray dataset. For example
to get sawnwood data with an instance of that object, use `gfpmx["sawn"]`. Then within a
product's dataset, for example sawnwood, access the two dimensional data array of
consumption as `gfpmx["sawn"]["cons"]`. That array is a panel dataset with a year and a
country dimension. Other arrays have only one country dimension, for example demand
elasticities. Xarray automatically aligns the dimensions when doing operations among
arrays.


# Input, output

Input data can be taken from any source of tabular data which python can deal with. For
example in the GFPMx model, data is contained in a single Excel spreadsheet file with
different sheets representing consumption, production, import, export and prices of the
major forest products available in FAOSTAT. An import script first converts these sheets
into csv files. The `gfpmx_data.py` module then loads these files into an Xarray data
structure as described in the representation section above.

The output data is saved to NetCDF files, which are the representation of Xarray on
disk. Although, not frequently used in economics, this format is widely used in earth
systems modelling. This makes it a good component in a system of models where economic
and biophysical model exchange data. A method called `write_datasets_to_netcdf` sets a
third dimension coordinate called `product` before saving the datasets to netcdf files.


# Implementation

As illustrated by the source code examples above, the labelled panel data structure
makes it possible to implement readable equations. Figure X illustrates the data
structure. There is an xarray dataset for each product. Many dataset and

The 1D data arrays are defined by country only. This means that elasticities do not
change across time. It would be possible to defined elasticities that change through
time by storing the elasticities in 2D objects instead.

Note: We have thought about setting the product as another dimension of a larger data
array that would contain all products, but we have decided against this because products
are treated differently and adding a third dimension to the data array would mean that
we need to call the 3 dimensions each time we write equations with these data arrays.
However, this decision can be revised and adding a third dimension could well be
experimented as further development of this model. As explained above, the method called
`write_datasets_to_netcdf` already sets a third dimension coordinate called `product`
before saving the datasets to netcdf files.


# Model run





# Visualisation

We can make use of Xarray's built-in visualisation capabilities to draw plots of the
data contained in these panel datasets.

TODO Figure


# Conclusion

We have created a new representation of panel datasets using N dimensional labelled data
arrays. The data structure enhances source code readability so that it can serve as the
basis for further modelling improvement and will facilitate the implementation of
different forest sector models re-using the cobwood framework.


# References


