#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Paul Rougieux.

JRC biomass Project.
Unit D1 Bioeconomy.

Reproduce the GFPMX model run by Joseph Buongiorno.
Originally released at
    https://buongiorno.russell.wisc.edu/gfpm/

Usage:
    >>> from gftmx.gfpmx_runner import gfpmx_runner
    >>> gfpmx_runner.run_step(year=2019)

"""

# Third party modules
import pandas

# Internal modules
from gftmx.gfpmx_data import gfpmx_data


class GFPMXRunner:
    """
    Reproduce the GFPMX model run
    """

    def __init__(self):
        """Initialise with historical data, before the model run"""
        self.swd_cons = (gfpmx_data.get_cons('SawnCons', 'SawnPrice')
                         .query("year <= @ gfpmx_data.base_year")
                         )

    def run_step(self, year):
        """Run the given year as a time step
        """
        # Add empty data for the given year based on the unique country names
        # and their related parameters that are not varying through time
        static_vars = ['id',  'price_elasticity', 'constant', 'gdp_elasticity', 'country']
        df = self.swd_cons[static_vars].drop_duplicates()
        assert len(df) == len(self.swd_cons.id.distinct())
        df['year'] = year
        self.swd_cons = pandas.concat([gfpmx_runner.swd_cons, df])


# Make a singleton #
gfpmx_runner = GFPMXRunner()
