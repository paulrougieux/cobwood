
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A script to save all sheets of the GFPMX Excel implementation to csv files

Author Paul Rougieux

See also the notebook that reproduces GFPM simulation.

"""

# Built-in modules #
from pathlib import Path
import os

# Third party modules #
import pandas
from tqdm import tqdm

# First party modules #

# Internal modules #
from gftmx.data_dir import gftmx_data_dir

# Input file
excel_file = "~/large_models/GFPMX-8-6-2021.xlsx"
# Output folder
gfpmx_data_dir = os.path.join(gftmx_data_dir, "gfpmx")
if not Path(gfpmx_data_dir).exists():
    Path(gfpmx_data_dir).mkdir(parents=True)

# Load the Excel file in a dictionary of data frames
gfpmx_data = pandas.read_excel(excel_file, sheet_name=None)
print(gfpmx_data.keys())

# Industrial roundwood production
gfpmx_data['IndroundProd'].to_csv(gfpmx_data_dir + "/" + "IndroundProd.csv")

# Write all sheets to csv files
for key in tqdm(gfpmx_data.keys()):
    df = gfpmx_data[key]
    # Remove empty columns in place
    df.dropna(how='all', axis=1, inplace=True)
    # Write the csv file
    df.to_csv(gfpmx_data_dir + "/" + key + ".csv", index=False)
