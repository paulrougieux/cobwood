#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Paul Rougieux.

JRC biomass Project.
Unit D1 Bioeconomy.

Download a compressed CSV file from the FAOSTAT API and save it in the data folder.

>>> from cobwood.faostat import faostat
>>> faostat.download("Forestry_E_All_Data_(Normalized).zip")

Read a compressed CSV

>>> from cobwood.faostat import faostat
>>> fo = faostat.read_csv("Forestry_E_All_Data_(Normalized).zip")
"""


# Third party modules
import re
import shutil
import urllib.request
from pathlib import Path
from zipfile import ZipFile
import pandas

# Internal modules
from cobwood import cobwood_data_dir

# Define a location to store data locally
faostat_data_folder = cobwood_data_dir / "faostat"
# Create the faostat data folder if it doesn't exist
if not Path(faostat_data_folder).exists():
    Path(faostat_data_folder).mkdir(parents=True)


class Faostat:
    """
    Download from the FAOSTAT API and store it.
    """

    # Define the location of the original source data
    url_base = "http://fenixservices.fao.org/faostat/static/bulkdownloads"
    # Define a location to store data locally
    data_folder = faostat_data_folder

    def download(self, file_name):
        """Download a compressed CSV file from the FAOSTAT API and save it in the data folder.

        Sample use

        >>> from cobwood.faostat import faostat
        >>> faostat.download("Forestry_E_All_Data_(Normalized).zip")
        """
        orig_url = self.url_base + "/" + file_name
        dest_file = self.data_folder + "/" + file_name
        # Define headers, otherwise faostat throws an Error 403: Forbidden
        # Based on https://stackoverflow.com/a/66591873/2641825
        header = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.11 (KHTML, like Gecko) "
            "Chrome/23.0.1271.64 Safari/537.11",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
            "Accept-Encoding": "none",
            "Accept-Language": "en-US,en;q=0.8",
            "Connection": "keep-alive",
        }
        # Request
        req = urllib.request.Request(url=orig_url, headers=header)
        with urllib.request.urlopen(req) as response:
            with open(dest_file, "wb") as f:
                shutil.copyfileobj(response, f)

    def read_csv(self, file_name):
        """Read a compressed CSV into a pandas data frame and rename its columns to snake case.

        Sample use

        >>> from cobwood.faostat import faostat
        >>> fo = faostat.read_csv("Forestry_E_All_Data_(Normalized).zip")
        """
        zip_file_name = self.data_folder + "/" + file_name
        # There are 2 csv files in the archive
        # Load the csv file with the same name as the archive itself
        csv_file_name = re.sub(".zip", ".csv", file_name)

        with ZipFile(zip_file_name).open(csv_file_name) as csv_file:
            df = pandas.read_csv(
                csv_file, sep=",", quotechar='"', encoding="ISO-8859-1"
            )
        # Rename columns to snake case
        df = df.rename(columns=lambda x: re.sub(r" ", "_", x).lower())
        return df


# Make a singleton #
faostat = Faostat()
