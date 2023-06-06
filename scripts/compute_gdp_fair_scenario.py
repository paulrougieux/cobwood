""" The purpose of this script is to use the GDP Fair scenario of Bodirsky et al 2022 as an
input to the GFPMx forest sector model

TODO 1 replace COUNTRIES by a list internal to the dataset for example
TODO 2 prepare the GFPMX object gfpmx_8_6_2021

Steps for the run:

1 Load GFPMx data GFPMX(
2 Load GDP Fair scenario data and readjust to the same GDP level as the
  historical series so that there is no discontinuity at the base year.
3 Create a GFPMX object with GFPMx data and GDP Fair data
4 Run the model with that GDP scenario
5 Save output to netcdf files. The GFPMX class should have a method that stores
  each dataset to a scenario output folder  :

    ds.to_netcdf("path/to/file.nc")

- Read the output later to plot the model results, starting with an overview of
  industrial roundwood and fuelwood harvest at EU level

    ds = xarray.open_dataset("path/to/file.nc")

Requirement prepare the data with:

    >>> from cobwood.gfpmx_spreadsheet_to_csv import gfpmx_spreadsheet_to_csv
    >>> gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-8-6-2021.xlsx")
    >>> gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-base2020.xlsx")
    >>> gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-base2021.xlsb")

    >>> from cobwood.gfpmx import GFPMX
    >>> # Load data for a base year in 2019
    >>> gfpmx_data = GFPMXData(data_dir="gfpmx_8_6_2021", base_year=2018)

Note: in CBM, the base year is the first year of the simulation, as illustrated
by the condition `if self.year < self.country.base_year` (in
`eu_cbm_hat/cbm/dynamic.py`) which governs the start of the harvest allocation
tool.

"""
