"""This scripts computes all GFPMx equations using xarray
"""

from gftmx.gfpmx_data import gfpmx_data

# Load data
sawn = gfpmx_data.convert_sheets_to_dataset("sawn")
panel = gfpmx_data.convert_sheets_to_dataset("panel", ["gdp"])


# Compute demand
