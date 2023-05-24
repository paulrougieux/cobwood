
This package implements a Cobweb version of the Global Forest Trade Model.

# Model Formulation

The model formulation is based on GFPMX: "A Cobweb Model of the Global Forest Sector,
with an Application to the Impact of the COVID-19 Pandemic" by Joseph Buongiorno
https://doi.org/10.3390/su13105507

The GFPMX input data and parameters are available as a spreadsheet at:
https://buongiorno.russell.wisc.edu/gfpm/


# Data

The data is based on the FAOSTAT forestry production and trade data set available at:
http://www.fao.org/faostat/en/#data/FO/visualize


# Xarray

An equation typically runs for 180 countries over 80 years. We implement each equation
over 2 dimensional data arrays where country names represent the first dimension (also
called coordinate) and years constitute the second dimension. Xarray data arrays can be
converted to a format similar to the original GFPMx spreadsheet with countries in rows
and years in columns. For example the following code uses `DataArray.to_pandas()` to
convert the pulp import array to a csv file using the pandas to_csv() method:

    from cobwood.gfpmx_data import GFPMXData
    gfpmx_data = GFPMXData(data_dir="gfpmx_8_6_2021", base_year = 2018)
    pulp = gfpmx_data.convert_sheets_to_dataset("pulp")
    pulp["imp"].to_pandas().to_csv("/tmp/pulp_imp.csv")

Example table containing the first few lines and columns:

| country | 2019 | 2020 | 2021 |
|---------|------|------|------|
| Algeria | 66   | 61   | 56   |
| Angola  | 0    | 0    | 0    |
| Benin   | 0    | 0    | 0    |

The `DataArray.to_dataframe()` method converts an array and its coordinates into a tidy
pandas.DataFrame in long format, starting with a country and a year column on the left.

    pulp["imp"].to_dataframe().to_csv("/tmp/pulp_imp_long.csv")

Example table containing the first few lines and columns:

| country | year | imp |
|---------|------|-----|
| Algeria | 2019 | 66  |
| Algeria | 2020 | 61  |
| Algeria | 2021 | 56  |

