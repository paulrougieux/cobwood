#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The script to save all sheets of the GFPMX Excel implementation to csv files
has been moved to cobwood/gfpmx_spreadsheet_to_csv.py

This script might remain useful to investigate issues with column names or sheet names.

"""
# Built-in modules #
from pathlib import Path
import re
import shutil

# Third party modules #
import pandas

# First party modules #

# Internal modules #

gfpmx_data_dir = None
gfpmx_excel_file = None

# Paste files to libcbm_data for the forest dynamics model
if False:
    dest_dir = Path.home() / "repos/eu_cbm/eu_cbm_data/domestic_harvest/cobwood"
    dest_dir.mkdir(exist_ok=True)
    # Renames those primary product files to "harvest"
    shutil.copy(gfpmx_data_dir / "fuelprod.csv", dest_dir / "fw_harvest.csv")
    shutil.copy(gfpmx_data_dir / "indroundprod.csv", dest_dir / "irw_harvest.csv")
    # Copy secondary product files
    production_files = [
        "panelprod.csv",
        "paperprod.csv",
        "pulpprod.csv",
        "roundprod.csv",
        "sawnprod.csv",
    ]
    for prod_file in production_files:
        shutil.copy(gfpmx_data_dir / prod_file, dest_dir / prod_file)

    print(f"Copied from {gfpmx_data_dir} to {dest_dir}")


# Investigate unnamed columns
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
