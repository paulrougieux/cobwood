#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Paul Rougieux.

JRC biomass Project.
Unit D1 Bioeconomy.

Reproduce the GFPMX model run by Joseph Buongiorno.
The model was originally released as spreadsheet formulas at
    https://buongiorno.russell.wisc.edu/gfpm/

Usage:
    >>> from gftmx.gfpmx_runner import gfpmx_runner
    >>> gfpmx_runner.run_next_step()

"""
# Internal modules
import logging

# Third party modules
import pandas

# Internal modules
from gftmx.gfpmx_data import gfpmx_data
import gftmx.logger

class GFPMXRunner:
    """
    Reproduce the GFPMX model run
    """

    def __init__(self):
        """Initialise with historical data, before the model run"""
        self.swd_cons = (gfpmx_data.get_cons('SawnCons', 'SawnPrice')
                         .query("year <= @ gfpmx_data.base_year")
                         )
        # Create logger with 'gftmx'
        self.logger = logging.getLogger('gftmx.gfpmx_runner')

    def run_next_step(self):
        """Run the next year based on the last year available in the data.
        """
        last_year = self.swd_cons.year.max()
        curr_year = last_year + 1
        self.logger.info("Running year %s.", curr_year)
        # Add empty data for the given year based on the unique country names
        # and their related parameters that are not varying through time
        static_vars = ['id',  'price_elasticity', 'constant', 'gdp_elasticity', 'country']
        df = self.swd_cons[static_vars].drop_duplicates()
        assert len(df) == len(self.swd_cons.id.unique())
        df['year'] = curr_year
        self.swd_cons = pandas.concat([gfpmx_runner.swd_cons, df])


# Make a singleton #
gfpmx_runner = GFPMXRunner()
