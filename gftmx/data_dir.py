#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Paul Rougieux.

JRC biomass Project.
Unit D1 Bioeconomy.
"""

# Build in modules
from pathlib import Path
import os

# Where is the data, default case #
gftmx_data_dir = Path("~/repos/gftmx_data/")

# But you can override that with an environment variable #
if os.environ.get("GFTMX_DATA"):
    gftmx_data_dir = Path(os.environ['GFTMX_DATA'])
