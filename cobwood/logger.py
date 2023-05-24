#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Paul Rougieux.

JRC biomass Project.
Unit D1 Bioeconomy.

Copied from https://docs.python.org/3/howto/logging-cookbook.html

Create a cobwood logger with file handler:

    >>> import cobwood.logger

This can be then used directly from any sub module:

    >>> import logging
    >>> logger = logging.getLogger('cobwood.sub_module')
    >>> logger.info("Doing this and that")

"""

# Third party modules
import logging

# Internal modules
from cobwood import cobwood_data_dir

# create logger with 'cobwood'
logger = logging.getLogger("cobwood")
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(cobwood_data_dir / "gfpmx.log")
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

logger.info(
    "Created a logger with file handler %s.", str(cobwood_data_dir / "gfpmx.log")
)
# Usage
# from cobwood.gfpmx_runner import gfpmx_runner
# logger.info('Calling gfpmx_runner.run_next_step().')
# gfpmx_runner.run_next_step()
# logger.info('Finished gfpmx_runner.run_next_step().')
