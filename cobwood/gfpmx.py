"""Run the GFPMX model

Run with xarray and compare to the reference dataset for each available model
version (with different base years)

    >>> from cobwood.gfpmx import GFPMX
    >>> # Base 2018
    >>> gfpmxb2018 = GFPMX(data_dir="gfpmx_8_6_2021", base_year=2018)
    >>> # Run and stop when the result diverges from the reference spreadsheet
    >>> gfpmxb2018.run(compare=True)
    >>> # Run and continue when the result diverges (just print the missmatch message)
    >>> gfpmxb2018.run(compare=True, strict=False)
    >>> # Just run, without comparison (default is compare=False)
    >>> gfpmxb2021.run()
    >>> print(gfpmxb2018.indround)
    >>> # Base 2020
    >>> gfpmxb2020 = GFPMX(data_dir="gfpmx_base2020", base_year=2020)
    >>> gfpmxb2020.run_and_compare_to_ref()
    >>> # Base 2021
    >>> gfpmxb2021 = GFPMX(data_dir="gfpmx_base2021", base_year=2021)
    >>> gfpmxb2021.run_and_compare_to_ref()

You can debug data issues by creating the data object only as follows:

    >>> from cobwood.gfpmx_data import GFPMXData
    >>> gfpmx_data_b2018 = GFPMXData(data_dir="gfpmx_8_6_2021", base_year=2018)

You can debug equations for the different model versions as follows:

    >>> from cobwood.gfpmx_equations import world_price
    >>> world_price(gfpmx_base_2018.sawn, gfpmx_base_2018.indround,2018)

 You will then be able to load Xarray datasets with the
`convert_sheets_to_dataset()` method:

    >>> from cobwood.gfpmx_data import GFPMXData
    >>> gfpmxb2018 = GFPMX(data_dir="gfpmx_8_6_2021", base_year=2018)
    >>> print(gfpmxb2018.other_ref)
    >>> print(gfpmxb2018.indround_ref)
    >>> print(gfpmxb2018.sawn_ref)
    >>> print(gfpmxb2018.panel_ref)
    >>> print(gfpmxb2018.pulp_ref)
    >>> print(gfpmxb2018.paper_ref)
    >>> print(gfpmxb2018.gdp)

"""

import cobwood
from cobwood.gfpmx_data import compare_to_ref
from cobwood.gfpmx_data import GFPMXData
from cobwood.gfpmx_data import remove_after_base_year_and_copy
from cobwood.gfpmx_data import convert_to_2d_array
from cobwood.gfpmx_equations import compute_one_time_step


class GFPMX:
    """
    Read data from the GFTMX data set.

    The GFTMX dataset was converted to csv files one for each sheet in the
    original Excel Spreadsheet. This singleton gives access to each file.

    Load sawnwood consumption data in long format:

    :param data_dir Location of the csv files
    :param base_year Simulation base year i.e. last year of historical data
           available in the spreadsheet

        >>> from cobwood.gfpmx_data import GFPMXData
        >>> gfpmx_data = GFPMXData(data_dir="gfpmx_8_6_2021", base_year = 2018)
        >>> swd_cons = gfpmx_data['sawncons']
        >>> swd_cons

    The GFPMX dataset is useful to:

        1. Verify the reproducibility of results given in the spreadsheet

        2. Reuse elasticities, tariffs, constants and other coefficients that cannot be
           estimated easily

    See also the script that moves data from the original Excel spreadsheet to CSV files:
    `scripts/gfpmx_spreadsheet_to_csv.py`
    """

    def __init__(self, data_dir, base_year):
        self.data_dir = cobwood.data_dir / data_dir
        self.base_year = base_year
        self.last_time_step = 2050
        # Data
        self.data = GFPMXData(data_dir=data_dir)

        # Load reference data
        self.other_ref = self.data.convert_sheets_to_dataset("other")
        self.indround_ref = self.data.convert_sheets_to_dataset("indround")
        self.fuel_ref = self.data.convert_sheets_to_dataset("fuel")
        self.sawn_ref = self.data.convert_sheets_to_dataset("sawn")
        self.panel_ref = self.data.convert_sheets_to_dataset("panel")
        self.pulp_ref = self.data.convert_sheets_to_dataset("pulp")
        self.paper_ref = self.data.convert_sheets_to_dataset("paper")
        self.gdp = convert_to_2d_array(self.data.get_sheet_wide("gdp"))

        # Keep only data before the base year
        self.other = remove_after_base_year_and_copy(self.other_ref, self.base_year)
        self.fuel = remove_after_base_year_and_copy(self.fuel_ref, self.base_year)
        self.indround = remove_after_base_year_and_copy(
            self.indround_ref, self.base_year
        )
        self.sawn = remove_after_base_year_and_copy(self.sawn_ref, self.base_year)
        self.panel = remove_after_base_year_and_copy(self.panel_ref, self.base_year)
        self.pulp = remove_after_base_year_and_copy(self.pulp_ref, self.base_year)
        self.paper = remove_after_base_year_and_copy(self.paper_ref, self.base_year)

    def run_and_compare_to_ref(self, rtol: float = None):
        """Takes a gpfmx_data object, remove data after the base year
        run the model and compare it to the reference dataset
        # TODO: decrease tolerance
        """
        self.run(compare=True, rtol=rtol)

    def run(self, compare: bool = False, rtol: float = 1e-2, strict: bool = True):
        """Run the model for many time steps from base_year + 1 to last_time_step."""
        if rtol is None:
            rtol = 1e-2

        # Add GDP projections to secondary products datasets.
        # GDP are projected to the future and `self.gdp` might be changed by
        # the user before the model run. This is why it is added only at this time.
        self.sawn["gdp"] = self.gdp
        self.panel["gdp"] = self.gdp
        self.fuel["gdp"] = self.gdp
        self.paper["gdp"] = self.gdp

        for this_year in range(self.base_year + 1, self.last_time_step + 1):
            print(this_year)
            compute_one_time_step(
                self.indround,
                self.fuel,
                self.pulp,
                self.sawn,
                self.panel,
                self.paper,
                self.other,
                this_year,
            )
            if compare:
                ciepp_vars = ["cons", "imp", "exp", "prod", "price"]
                compare_to_ref(
                    self.sawn,
                    self.sawn_ref,
                    ciepp_vars,
                    this_year,
                    rtol=rtol,
                    strict=strict,
                )
                compare_to_ref(
                    self.panel,
                    self.panel_ref,
                    ciepp_vars,
                    this_year,
                    rtol=rtol,
                    strict=strict,
                )
                compare_to_ref(
                    self.paper,
                    self.paper_ref,
                    ciepp_vars,
                    this_year,
                    rtol=rtol,
                    strict=strict,
                )
                compare_to_ref(
                    self.pulp,
                    self.pulp_ref,
                    ciepp_vars,
                    this_year,
                    rtol=rtol,
                    strict=strict,
                )
                compare_to_ref(
                    self.indround,
                    self.indround_ref,
                    ciepp_vars,
                    this_year,
                    rtol=rtol,
                    strict=strict,
                )
                compare_to_ref(
                    self.fuel,
                    self.fuel_ref,
                    ciepp_vars,
                    this_year,
                    rtol=rtol,
                    strict=strict,
                )
                compare_to_ref(
                    self.other,
                    self.other_ref,
                    ["stock"],
                    this_year,
                    rtol=rtol,
                    strict=strict,
                )
