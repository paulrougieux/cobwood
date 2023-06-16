#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The script to save all sheets of the GFPMX Excel implementation to csv files
has been moved to a function inside cobwood/gfpmx_spreadsheet_to_csv.py

Usage:

    ipython  -i  ~/repos/cobwood/scripts/gfpmx_data_to_csv.py

This script might remain useful to investigate issues with column names or sheet names.

"""

import re
import pandas

import cobwood
from cobwood.gfpmx_spreadsheet_to_csv import gfpmx_spreadsheet_to_csv

#########################################
# Convert the Excel spreadsheets to CSV #
#########################################
gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-8-6-2021.xlsx")
gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-base2020.xlsx")
gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-base2021.xlsb")


###############################
# Investigate unnamed columns #
###############################
gfpmx_data_dir = cobwood.data_dir
gfpmx_excel_file = None

# key = "IndroundProd"
if False:
    for key in gfpmx_excel_file.keys():
        print(f"\n**{key}**")
        if key in ["FuelProd$", "IndroundProd$"]:
            print("lala")
        df = gfpmx_excel_file[key]
        # Those operations are duplicated from above
        # Remove empty columns in place
        df.dropna(how="all", axis=1, inplace=True)
        # Rename columns to snake case, replace all non alphanumeric characters by an underscore
        df.rename(columns=lambda x: re.sub(r"\W+", "_", str(x)).lower(), inplace=True)
        # Rename unnamed columns if they have unique values
        unnamed = df.filter(regex="unnamed").columns.to_list()
        for col in unnamed:
            content = df[col].dropna()
            new_name = col
            if len(content.unique()) != 1 or not pandas.api.types.is_string_dtype(
                content
            ):
                break
            if content.str.contains("m3").all():
                new_name = "unit"
            if content.str.contains(r"[^\W\d_]").all():
                new_name = "element"
            print(
                f"Old name: '{col}' content: {content.unique()}, new name: '{new_name}'"
            )
