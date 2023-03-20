#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Location of the data
"""

# Build in modules
from pathlib import Path
import os

# Where is the data, default case #
data_dir = Path("~/repos/gftmx_data/")

# But you can override that with an environment variable #
if os.environ.get("GFTMX_DATA"):
    data_dir = Path(os.environ["GFTMX_DATA"])

# For backward compatibility
# TODO: remove when it is replaced everywhere by gftmx.data_dir
gftmx_data_dir = data_dir
