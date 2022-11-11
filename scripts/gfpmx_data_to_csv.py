#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A script to save all sheets of the GFPMX Excel implementation to csv files

Typically you would run this file from a command line like this:

     ipython -i ~/rp/gftmx/scripts/gfpmx_data_to_csv.py

Source of the GFPMX spread sheet data by Joseph Buongiorno:
    https://buongiorno.russell.wisc.edu/gfpm/

Author of this script Paul Rougieux

See also the scripts that reproduces the GFPM simulation:

    ~/rp/gftmx/scripts/compute_swd_equations.py

"""

# Built-in modules #
from pathlib import Path
import re
import shutil

# Third party modules #
import pandas
from tqdm import tqdm

# First party modules #

# Internal modules #
from gftmx.data_dir import gftmx_data_dir

# Input file from https://buongiorno.russell.wisc.edu/gfpm/
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
    df.dropna(how="all", axis=1, inplace=True)
    # Rename columns to snake case, replace all non alphanumeric characters by an underscore
    df.rename(columns=lambda x: re.sub(r"\W+", "_", str(x)).lower(), inplace=True)
    # Add "value" prefix to year columns in preparation for a reshape from wide to long
    df.rename(columns=lambda x: re.sub(r"^(\d{4})$", r"value\1", x), inplace=True)
    # Rename element and unit columns
    df.rename(columns={"unnamed_1": "element", "unnamed_2": "unit"}, inplace=True)
    # Rename the column that contains the industrial roundwood world price elasticity
    products_equation_10 = ["FuelPrice", "SawnPrice", "PanelPrice", "PulpPrice"]
    if key in products_equation_10:
        selector = df["unnamed_4"].astype(str).str.contains("ound")
        if any(selector):
            df = df.rename(columns={"unnamed_4": "rwdelast"})
    # Harmonize product names
    if "faostat_name" in df.columns:
        if df["faostat_name"].unique().tolist() == ["Sawnwood"]:
            df["faostat_name"] = "Sawnwood+sleepers"

    # Further renaming for the purpose of libcbm usage
    if key in ["FuelProd", "IndroundProd"]:
        df.faostat_name = df.faostat_name.ffill()
        df.element = df.element.ffill()
        df.unit = df.unit.ffill()
        cols = df.columns.tolist()
        df["scenario"] = "reference"
        df = df[["scenario"] + cols]
    # Write the csv file
    csv_file_name = re.sub(r"\$", r"_usd", key).lower() + ".csv"
    csv_file_name = Path(gfpmx_data_dir) / csv_file_name
    df.to_csv(csv_file_name, index=False)

# Paste files to libcbm_data for the forest dynamics model
if False:
    dest_dir = Path.home() / "repos/libcbm_data/common/gftmx"
    dest_dir.mkdir(exist_ok=True)
    for file_name in ["fuelprod.csv", "indroundprod.csv"]:
        from_path = gfpmx_data_dir / file_name
        to_path = dest_dir / file_name
        shutil.copy(from_path, to_path)
        print(f"Copied {from_path} to {to_path}")


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
