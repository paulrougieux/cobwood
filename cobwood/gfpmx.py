"""Run the GFPMX model and store output data

"""

import cobwood
from cobwood.gfpmx_data import compare_to_ref
from cobwood.gfpmx_data import GFPMXData
from cobwood.gfpmx_data import remove_after_base_year_and_copy
from cobwood.gfpmx_data import convert_to_2d_array
from cobwood.gfpmx_equations import compute_one_time_step


class GFPMX:
    """
     GFPMX model simulation object.

     - Reads data from the GFPMXData object
     - Runs the model
     - Saves the model output in NETCDF files

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
         >>> gfpmxb2020.run_and_compare_to_ref() # Fails
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

    Dynamic Attributes:
         sawn: Sawnwood data
         fuel: Fuelwood data

    """

    def __init__(self, data_dir, base_year):
        self.input_data_dir = cobwood.data_dir / data_dir
        self.base_year = base_year
        self.last_time_step = 2070
        self.input_data = GFPMXData(data_dir=data_dir)
        self.products = ["indround", "fuel", "sawn", "panel", "pulp", "paper"]

        # Load reference data
        for product in self.products + ["other"]:
            self[product + "_ref"] = self.input_data.convert_sheets_to_dataset(product)
        self["gdp"] = convert_to_2d_array(self.input_data.get_sheet_wide("gdp"))

        # Keep only data before the base year
        for product in self.products + ["other"]:
            self[product] = remove_after_base_year_and_copy(
                self[product + "_ref"], self.base_year
            )

    def __getitem__(self, key):
        """Get a dataset from the data dictionary"""
        return getattr(self, key, None)

    def __setitem__(self, key, value):
        """Set a dataset from the data dictionary"""
        setattr(self, key, value)

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
            print(f"Computing: {this_year}", end="\r")
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
                for product in self.products:
                    compare_to_ref(
                        self[product],
                        self[product + "_ref"],
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
