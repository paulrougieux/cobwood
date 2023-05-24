#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Location of the data
"""

# Build in modules
from pathlib import Path
import os

# Where is the data, default case #
data_dir = Path("~/repos/cobwood_data/")

# But you can override that with an environment variable #
if os.environ.get("COBWOOD_DATA"):
    data_dir = Path(os.environ["COBWOOD_DATA"])

# For backward compatibility
# TODO: remove when it is replaced everywhere by cobwood.data_dir
cobwood_data_dir = data_dir
