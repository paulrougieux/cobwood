---
title: 'Cobwood: model macroeconomic wood consumption with the python package Xarray'
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



# Statement of need

Trees take many decades to grow, and wood demand is globalized. To help manage large
forest ecosystems over the long term, decision makers need to know the global
consumption and trade in forest products and to envision what could be potential future
developments. This is why forest economists have developed macroeconomic models of the
forest sector.

The following forest sector models are available at the global level: the Global Forest
Products Model (GFPM), the EFI-GTM (European Forest Institute Global Trade Model), the
G4M, The Global Forest Trade Model (GFTM). There are many other forest sector models at
the regional or national level.

Within these models, macroeconomic datasets are structured with country and time
dimension, this structure is called a **panel data** structure in econometrics. Typical
representation in statistical modelling software lacks a labelled panel data structure,
instead, they have partial data labelling with matrices or data frames floating around
the modelling script. This makes these programs nicely concise, but harder to read for
the uninitiated. See for example the Matlab source code of the GFTM, or the source code
of G4M.

We have used the labelled data arrays from Xarray to represent panel data. This gives us
the possibility to use the time and countries dimensions to write equations in python
that are parallel to the mathematical equations in the sources paper. This similarity
between equations and python code results in a results in a more readable implementation
of the modelling equation. On the output side, the data structure can be saved as NetCDF
files, with added metadata labels on units. This provides a solid ground for
reproducibility of analysis by other researchers teams.


# Represent panel data with Xarray

The cobwood package is extensible and can be used to represent different models, but the
first version only contains one model: the Global Forest Products Model called GFPMx
[@buongiorno2021gfpmx]. The cobwood package contains a `GFPMX` object that represents
global forest products consumption, production, import, export and prices of forest
products. Each product is represented as a separate Xarray dataset. For example to get
sawnwood data with an instance of that object, use `gfpmx["sawn"]`. Then within a
product's dataset, for example sawnwood, access the two dimensional data array of
consumption as `gfpmx["sawn"]["cons"]`. That array is a panel dataset with a year and a
country dimension. Other arrays have only one country dimension, for example demand
elasticities. Xarray auto aligns the dimensions when doing operations among arrays.


# Implement and run a model


# Input Output

Input data can be taken from any source of table data which python can deal with. For
example in the GFPMx model, data is contained in a single Excel spreadsheet file with
different sheets representing consumption, production, import, export and prices of the
major forest products available in FAOSTAT. An import script first converts these sheets
into csv files. The `gfpmx_data.py` module then loads these files into an Xarray data
structure as described in the representation section above.

The output data is saved to NetCDF files, which are the representation of Xarray on
disk. Although, not frequetly used in economics, this format is widely used in earth
systems modelling. This makes it a good component in a system of models where economic
and biophysical model exchange data.


# Conclusion

This data structure can serve as the basis for further modelling improvement and should
facilitate the implementation of different forest sector models within the same
framework.


# References


