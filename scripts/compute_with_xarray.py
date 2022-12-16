#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A script to compute GFPMX equations using xarray

Run this file with:

     ipython -i ~/repos/gftmx/scripts/compute_with_xarray.py


The first attempt is the easiest one based on the long format. But since it is based on the long
format, we loose the units. It would be nice to have the units as dataset
attribute to each data array

    sawn_ds.attrs["units"] = "test"
    sawn_ds.price.attrs["units"] = "$/m3"

The third attempt distinguishes:
- two dimensional data such as production, consumption or prices
- one dimensional data such as price elasticities which are defined by country
- attributes such as units

"""

# Third party modules
import xarray
import pandas

from gftmx.gfpmx_data import gfpmx_data

# Load data
indround_agg = gfpmx_data.get_agg_rows("indround")
pulp_agg = gfpmx_data.get_agg_rows("pulp")
pulp = gfpmx_data.get_country_rows("pulp", ["gdp"])
sawn = gfpmx_data.get_country_rows("sawn", ["gdp"])
sawn_agg = gfpmx_data.get_agg_rows("sawn", ["gdp"])
fuel = gfpmx_data.get_country_rows("fuel", ["gdp"])
fuel_agg = gfpmx_data.get_agg_rows("fuel", ["gdp"])
# TODO: remove rows containing "World prod/cons" or simply that don't have a
# FAOSTAT name from the input data pre-processed in
# "~/rp/gftmx/scripts/gfpmx_data_to_csv.py"
panel = gfpmx_data.get_country_rows("panel", ["gdp"])
panel_agg = gfpmx_data.get_agg_rows("panel", ["gdp"])
paper = gfpmx_data.get_country_rows("paper", ["gdp"])
paper_agg = gfpmx_data.get_agg_rows("paper", ["gdp"])

##################################################################
# First attempt convert data frames into datasets or data arrays #
##################################################################

# "Convert a pandas.DataFrame into an xarray.Dataset
#
#    Each column will be converted into an independent variable in the
#    Dataset. If the dataframe's index is a MultiIndex, it will be expanded
#    into a tensor product of one-dimensional indices (filling in missing
#    values with NaN). This method will produce a Dataset very similar to
#    that on which the 'to_dataframe' method was called, except with
#    possibly redundant dimensions (since all dataset variables will have
#    the same dimensionality)
sawn_ds = xarray.Dataset.from_dataframe(sawn)
sawn_ds

# class DataArray
# to_pandas(self) -> 'DataArray | pd.Series | pd.DataFrame'
#     Convert this array into a pandas object with the same shape.
#     The type of the returned object depends on the number of DataArray
#     dimensions:
#     * 0D -> `xarray.DataArray`
#     * 1D -> `pandas.Series`
#     * 2D -> `pandas.DataFrame`
#     Only works for arrays with 2 or fewer dimensions.
#     The DataArray constructor performs the inverse transformation.
sawn_da_dumb = xarray.DataArray(sawn)
sawn_da_dumb

# Convert
# See help(sawn_ds.to_stacked_array)

# I don't manage to use to_stacked_array
# sawn_ds[["price", "prod", "faostat_name"]].to_stacked_array("variable","faostat_name")
# ValueError: All variables in the dataset must contain the dimensions ('year', 'country').

# Convert data set to array
sawn_da = sawn_ds[["price", "prod"]].to_array("variable")

index = ["year", "country", "faostat_name"]
sawn_ds2 = xarray.Dataset.from_dataframe(sawn.reset_index().set_index(index))
sawn_da2 = sawn_ds2[["price", "prod"]].to_array("variable")

# Display index values
sawn_ds2.indexes["year"]
sawn_ds2.indexes["country"]

index = ["year", "country", "faostat_name"]
fuel_ds2 = xarray.Dataset.from_dataframe(fuel.reset_index().set_index(index))
fuel_da2 = fuel_ds2[["price", "prod"]].to_array("variable")


########################################################
# Second attempt build data array from the wide format #
########################################################
sawn_price_wide = gfpmx_data.get_sheet_wide("sawnprice")
index = [
    "faostat_name",
    "element",
    "unit",
    "input_elast",
    "world_price_elasticity",
    "constant",
    "country",
]
sawn_price_da = xarray.DataArray(
    sawn_price_wide.set_index(index), dims=["dim_0", "year"]
)

# Data for the first year
sawn_price_da[:, 0]
sawn_price_da.loc[:, "value1992"]
# N'importe quoi
# sawn_price_da.to_dataset(dim="dim_0").to_dataframe()


####################################################################################
# Third attempt panel 2 dimensions, elasticities 1 dimension and unit as attribute #
####################################################################################
sawn_price_wide = gfpmx_data.get_sheet_wide("sawnprice")


def convert_to_2d_array(df: pandas.DataFrame) -> xarray.DataArray:
    """Convert the year columns of a data frame to a two dimensional data array
    In wide format the values are in one column for each year.
    """
    cols = df.columns
    value_cols = cols[df.columns.str.contains("value")]
    da = xarray.DataArray(df.set_index("country")[value_cols], dims=["country", "year"])
    # Change year to an integer
    da["year"] = da["year"].str.replace("value", "").astype(int)
    # Store the unit as an attribute
    da.attrs["unit"] = sawn_price_wide["unit"].unique()
    return da


spda = convert_to_2d_array(sawn_price_wide)


def convert_to_1_dim_array(df: pandas.DataFrame, var: str) -> xarray.DataArray:
    """Convert one column of a data frame to a one dimensional data array"""
    return xarray.DataArray(df.set_index(index)[var], dims=["country"])


convert_to_1_dim_array(sawn_price_wide, "world_price_elasticity")
convert_to_1_dim_array(sawn_price_wide, "constant")

# Combine into a dataset
spds = xarray.Dataset(
    dict(
        price=spda,
        elast=convert_to_1_dim_array(sawn_price_wide, "world_price_elasticity"),
        constant=convert_to_1_dim_array(sawn_price_wide, "constant"),
    )
)

# Compute demand
t = 2019
spds.constant * spds.price.loc[dict(year=t)]
# .loc[dict(lon=260, lat=30)]


#############
# Questions #
#############
# How to put the year first, before the country?
# So it's compatible with compute_all_equations.py
# Maybe using assign_coords?
# https://docs.xarray.dev/en/stable/generated/xarray.DataArray.assign_coords.html#xarray.DataArray.assign_coords
# The fact that country is first, is because country are in rows and years in columns in the input data.
# Maybe this is better this way?
spda.loc["Algeria", "value1992"]
