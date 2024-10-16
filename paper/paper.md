---
title: 'Cobwood: a python package to represent macroeconomic wood consumption, production and trade with Xarray'
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

- TODO: Extract documentation from the package docstrings with pdoc

        pdoc -o public ./cobwood/

- TODO: install the package in a new environment, based on the TOML file

End comments.
-->

# Summary



# Statement of need

Panel data used in

is very structure, but typical representation in statistical modelling software lacks a
labelled structure, many matrices or data frames floating around the modelling script.
Xarray provides a very structure representation that
results in a more readable implementation of the modelling equation.


# Represent panel data with Xarray

The cobwood package is extensible and can be used to represent different models, but the
first version only contains one model: the Global Forest Products Model called GFPMx
[@buongiorno2021gfpmx]. The `GFPMX` object represents each product as a separate Xarray
dataset. For example to get sawnwood data with an instance of that object, use
`gfpmx["sawn"]`. Within a product's dataset, for example sawnwood, accessed as



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


