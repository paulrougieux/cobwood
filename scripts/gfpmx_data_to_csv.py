#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A script to save all sheets of the GFPMX Excel implementation to csv files

Typically you would run this file from a command line like this:

     ipython -i ~/rp/gftmx/scripts/gfpmx_data_to_csv.py

Source of the GFPMX spread sheet data by Joseph Buongiorno:
    https://buongiorno.russell.wisc.edu/gfpm/

Author of this script Paul Rougieux

See also the notebook that reproduces the GFPM simulation:
"""

# Built-in modules #
from pathlib import Path
import re

# Third party modules #
import pandas
from tqdm import tqdm

# First party modules #

# Internal modules #
from gftmx.data_dir import gftmx_data_dir

# Input file
excel_file = "~/large_models/GFPMX-8-6-2021.xlsx"
# Output folder
gfpmx_data_dir = Path(gftmx_data_dir) / "gfpmx"
if not Path(gfpmx_data_dir).exists():
    Path(gfpmx_data_dir).mkdir(parents=True)

print(f"\nLoad the Excel file {excel_file} in a dictionary of data frames")
gfpmx_excel_file = pandas.read_excel(excel_file, sheet_name=None)
print(gfpmx_excel_file.keys())

print("\nWrite all sheets to csv files in the output folder")
for key in tqdm(gfpmx_excel_file.keys()):
    df = gfpmx_excel_file[key]
    # Remove empty columns in place
    df.dropna(how='all', axis=1, inplace=True)
    # Rename columns to snake case
    df.rename(columns=lambda x: re.sub(r' ', '_', str(x)).lower(), inplace=True)
    # Add "value" prefix to year columns in preparation for a reshape from wide to long
    df.rename(columns=lambda x: re.sub(r'^(\d{4})$', r'value\1', x), inplace=True)
    # Write the csv file
    csv_file_name = Path(gfpmx_data_dir) / (key + ".csv")
    df.to_csv(csv_file_name, index=False)
