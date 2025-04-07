"""Run the GFPMX model

Usage:

    >>> ipython -i ~/repos/cobwood/scripts/run_gfpmx.py

"""
# from cobwood.gfpmx_spreadsheet_to_csv import gfpmx_spreadsheet_to_csv
# from cobwood.gfpmx_data import GFPMXData
from cobwood.gfpmx import GFPMX

########################################
# Convert the Excel spreadsheet to CSV #
########################################
# gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-8-6-2021.xlsx")
# gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-base2020.xlsx")
# gfpmx_spreadsheet_to_csv("~/large_models/GFPMX-base2021.xlsb")

###################################################
# Load data only to debug dataset creation issues #
###################################################
# gfpmx_data_b2018 = GFPMXData(data_dir="gfpmx_8_6_2021")
# gfpmx_data_b2020 = GFPMXData(data_dir="gfpmx_base2020")
# gfpmx_data_b2021 = GFPMXData(data_dir="gfpmx_base2021")

#############################
# Instantiate model objects #
#############################
# gfpmxb2018 = GFPMX(data_dir="gfpmx_8_6_2021", base_year=2018)
# gfpmxb2020 = GFPMX(data_dir="gfpmx_base2020", base_year=2020)
gfpmxb2021 = GFPMX(
    input_dir="gfpmx_base2021", base_year=2021, scenario="base_2021", rerun=True
)

#######
# Run #
#######
gfpmxb2021.run(compare=True, strict=False)
