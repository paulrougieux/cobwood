#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A script to save all sheets of a GFPMX Excel files into csv files.


Usage example on all available GFPMX spreadsheets:

    >>> from cobwood.gfpmx_spreadsheet_to_csv import gfpmx_spreadsheet_to_csv
    >>> gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-8-6-2021.xlsx")
    >>> gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-base2020.xlsx")
    >>> gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-base2021.xlsb")

Note the last file is an `xlsb` in binary format. You might get an ImportError:
Missing optional dependency 'pyxlsb'. Use pip or conda to install pyxlsb.

It can also be used as a script directly to export the default spreadsheet to csv:

    ipython -i ~/repos/cobwood/cobwood/gfpmx_spreadsheet_to_csv.py

Source of the GFPMX spread sheet data by Joseph Buongiorno:
    https://buongiorno.russell.wisc.edu/gfpm/

"""

# Built-in modules #
from pathlib import Path
import re

# Third party modules #
import pandas
from tqdm import tqdm

# First party modules #

# Internal modules #
import cobwood


def extract_world_price_parameter(df, col_name, contains, var_name):
    """Extract world price parameters such as input elasticity,
    stock elasticity and trend.
    """
    selector = df[col_name].astype(str).str.contains(contains)
    if any(selector):
        df = df.rename(columns={col_name: var_name})
        # Force variable type to numeric
        df[var_name] = pandas.to_numeric(df[var_name], errors="coerce")
    return df


def gfpmx_spreadsheet_to_csv(spreadsheet_path):
    """Convert GFTMX data to csv files and store them inside the cobwood_data directory

    The function gfpmx_spreadsheet_to_csv loads a Excel file and writes all
    sheets into individual CSV files. The CSV files are saved inside
    gfpmx_data_dir under a subdirectory name that correspond to the input file
    name converted to lower case. Different calls to this function can load 2
    or more different input files  based on different input Excel files.

    Usage:

        >>> from cobwood.gfpmx_spreadsheet_to_csv import gfpmx_spreadsheet_to_csv
        >>> gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-8-6-2021.xlsx")
        >>> gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-base2020.xlsx")
        >>> gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-base2021.xlsb")

    """
    # Convert the input file name to snake case. Use this as the output directory name.
    gfpmx_data_dir = re.sub(r"\W+", "_", Path(spreadsheet_path).stem).lower()
    gfpmx_data_dir = cobwood.data_dir / "gfpmx_input" / gfpmx_data_dir
    if not gfpmx_data_dir.exists():
        gfpmx_data_dir.mkdir(parents=True)
    print(f"\nLoad the Excel file {spreadsheet_path} in a dictionary of data frames.")
    gfpmx_excel_file = pandas.read_excel(spreadsheet_path, sheet_name=None)
    print(gfpmx_excel_file.keys())
    print(f"\nWrite all sheets to csv files in the output folder\n{gfpmx_data_dir}")
    for key in tqdm(gfpmx_excel_file.keys()):
        df = gfpmx_excel_file[key]
        # Remove empty columns in place
        df.dropna(how="all", axis=1, inplace=True)
        # Rename columns to snake case, replace all non alphanumeric characters by an underscore
        df.rename(columns=lambda x: re.sub(r"\W+", "_", str(x)).lower(), inplace=True)
        # Add "value" prefix to year columns in preparation for a reshape from wide to long
        df.rename(columns=lambda x: re.sub(r"^(\d{4})$", r"value_\1", x), inplace=True)
        # Rename element and unit columns
        df.rename(columns={"unnamed_1": "element", "unnamed_2": "unit"}, inplace=True)
        # Rename the column that contains the world price elasticity of the input
        # Equation 9 World Price of Industrial Roundwood
        # Equation 10 industrial roundwood world price elasticity
        # Equation 11 pulp world price elasticity
        price_tables = [
            "FuelPrice",
            "SawnPrice",
            "PanelPrice",
            "PulpPrice",
        ]
        if key in price_tables:
            df = extract_world_price_parameter(df, "unnamed_4", "ound", "input_elast")
        if key == "PaperPrice":
            df = extract_world_price_parameter(df, "unnamed_4", "ulp", "input_elast")
        if key == "IndroundPrice":
            df = extract_world_price_parameter(df, "unnamed_3", "trend", "trend")
            df = extract_world_price_parameter(df, "unnamed_4", "stock", "stock_elast")
        if key == "IndroundExp":
            if "marginal_propensity_to_export" not in df.columns:
                df.rename(
                    columns={"unnamed_5": "marginal_propensity_to_export"}, inplace=True
                )
            if "constant" not in df.columns:
                df.rename(columns={"unnamed_6": "constant"}, inplace=True)

        # This applies to product sheets, which have a "faostat_name" column
        if "faostat_name" in df.columns:
            # Harmonize product names
            if df["faostat_name"].unique().tolist() == ["Sawnwood"]:
                df["faostat_name"] = "Sawnwood+sleepers"

            # Fix typo in roundwood name
            df["faostat_name"].replace({"Roundwwood": "Roundwood"}, inplace=True)

            # Remove rows that don't have a faostat_name
            # They usually contain quality checks such as
            # World prod/cons or Worldexp/Worldimp
            df = df[~df["faostat_name"].isna()].copy()

        # Harmonize column names
        if "world_elasticity" in df.columns:
            df.rename(
                columns={"world_elasticity": "world_price_elasticity"}, inplace=True
            )
        if "stock_growth_rate_without_harvest" in df.columns:
            df.rename(
                columns={
                    "stock_growth_rate_without_harvest": "growth_rate_without_harvest"
                },
                inplace=True,
            )
        # Capitalize WORLD
        # It's written "World" in "FuelPrice" GFPMX base 2021
        if "country" in df.columns:
            df["country"] = df["country"].replace("World", "WORLD")

        # Further renaming for the purpose of libcbm usage
        if key in ["FuelProd", "IndroundProd"]:
            df.faostat_name = df.faostat_name.ffill()
            df.element = df.element.ffill()
            df.unit = df.unit.ffill()
        # Write the csv file
        csv_file_name = re.sub(r"\$", r"_usd", key).lower() + ".csv"
        csv_file_name = Path(gfpmx_data_dir) / csv_file_name
        df.to_csv(csv_file_name, index=False)


if __name__ == "__main__":
    # Input file from https://buongiorno.russell.wisc.edu/gfpm/
    gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-8-6-2021.xlsx")
