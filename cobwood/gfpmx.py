"""Run the GFPMX model and store output data

"""
import json
import xarray
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
        >>> # Base 2021
        >>> gfpmxb2021 = GFPMX(input_dir="gfpmx_base2021", base_year=2021, scenario_name="base_2021", rerun=True)
        >>> gfpmxb2021.run_and_compare_to_ref()
        >>> gfpmxb2021.run()

    Load output data, after a run has already been completed

        >>> gfpmx_pikssp2 = GFPMX(input_dir="gfpmx_base2021", base_year=2021, scenario_name="pikssp2_fel1")

    You can debug data issues by creating the data object only as follows:

        >>> from cobwood.gfpmx_data import GFPMXData
        >>> gfpmx_data_b2018 = GFPMXData(data_dir="gfpmx_8_6_2021", base_year=2018)

    You can debug equations for the different model versions as follows:

        >>> from cobwood.gfpmx_equations import world_price
        >>> world_price(gfpmx_base_2018.sawn, gfpmx_base_2018.indround,2018)

    Run other base years and compare GFPMx Excel results with the one from the cobwood

        >>> # Base 2018
        >>> gfpmxb2018 = GFPMX(input_dir="gfpmx_8_6_2021", base_year=2018, scenario_name="base_2018")
        >>> # Run and stop when the result diverges from the reference spreadsheet
        >>> gfpmxb2018.run(compare=True)
        >>> # Run and continue when the result diverges (just print the missmatch message)
        >>> gfpmxb2018.run(compare=True, strict=False)
        >>> # Just run, without comparison (default is compare=False)
        >>> gfpmxb2021.run()
        >>> print(gfpmxb2018.indround)
        >>> # Base 2020
        >>> gfpmxb2020 = GFPMX(input_dir="gfpmx_base2020", base_year=2020, scenario_name="base_2020")
        >>> gfpmxb2020.run_and_compare_to_ref() # Fails
        >>> gfpmxb2021 = GFPMX(input_dir="gfpmx_base2021", base_year=2021, scenario_name="base_2021")

    You will then be able to load Xarray datasets with the
    `convert_sheets_to_dataset()` method:

        >>> from cobwood.gfpmx_data import GFPMXData
        >>> gfpmxb2018 = GFPMX(input_dir="gfpmx_8_6_2021", base_year=2018)
        >>> print(gfpmxb2018.other_ref)
        >>> print(gfpmxb2018.indround_ref)
        >>> print(gfpmxb2018.sawn_ref)
        >>> print(gfpmxb2018.panel_ref)
        >>> print(gfpmxb2018.pulp_ref)
        >>> print(gfpmxb2018.paper_ref)
        >>> print(gfpmxb2018.gdp)
    """

    def __init__(self, input_dir, base_year, scenario_name, rerun=False):
        # TODO: change this so that it is initialised with a scenario_name only
        # The input_dir and base_year parameters should be in a yaml configuration
        # file associated with that scenario_name inside cobwood_data
        # See https://gitlab.com/bioeconomy/cobwood/cobwood/-/issues/10
        self.input_data = GFPMXData(data_dir=input_dir)
        self.output_dir = cobwood.data_dir / "gfpmx_output" / scenario_name
        self.combined_netcdf_file_path = self.output_dir / "combined_datasets.nc"
        self.base_year = base_year
        self.last_time_step = 2070
        self.scenario_name = scenario_name
        self.products = ["indround", "fuel", "sawn", "panel", "pulp", "paper"]

        # Load reference data
        for product in self.products + ["other"]:
            self[product + "_ref"] = self.input_data.convert_sheets_to_dataset(product)
        self["gdp"] = convert_to_2d_array(self.input_data.get_sheet_wide("gdp"))

        # If the output directory already exists, load data from the netcdf
        # output files, unless explicitly asked to rerun the simulation.
        if self.output_dir.exists() and not rerun:
            print(f"Loading simulation output from netcdf files in {self.output_dir}.")
            self.read_datasets_from_netcdf()
        else:
            # If asked to rerun the first message should not appear
            msg = ""
            if not rerun:
                msg = "There is no output from a previous run for this scenario "
                msg += f"'{self.scenario_name}'.\n"
            msg += f"Load input data from {input_dir} and reset time series to a "
            msg += f"base year {self.base_year} before simulation start."
            print(msg)
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

    def run_and_compare_to_ref(self, *args, **kwargs):
        """Takes a gpfmx_data object, remove data after the base year
        run the model and compare it to the reference dataset
        """
        self.run(compare=True, *args, **kwargs)

    def run(self, compare: bool = False, rtol: float = None, strict: bool = True):
        """Run the model for many time steps from base_year + 1 to last_time_step."""
        if rtol is None:
            rtol = 1e-2
        print(f"Running {self.scenario_name}")
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
        # Save simulation output
        self.write_datasets_to_netcdf()

    def write_datasets_to_netcdf(self):
        """Write all datasets to a single netcdf file with an extra 'product'
        dimension.

        This should be performed after the simulation run, to preserve the
        output of a given scenario. The GFPMX class contains one dataset for
        each product. This method combines them into one combined dataset with
        a new product dimension. It then saves that combined dataset to a
        NetCDF file.
        """
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True)

        datasets_to_combine = []
        attributes_dict = {}

        for product in self.products:
            # Assign a new coordinate 'product' to each Dataset
            ds = self[product].assign_coords(product=product)
            # Expand dimensions to include 'product'
            ds = ds.expand_dims("product")
            datasets_to_combine.append(ds)
            # Save attributes
            attributes_dict[product] = ds.attrs

        # Concatenate along the new 'product' dimension
        combined_ds = xarray.concat(datasets_to_combine, dim="product")
        # Store attributes as a global attribute in the combined dataset
        attributes_json_str = json.dumps(attributes_dict)
        combined_ds.attrs["individual_dataset_attributes"] = attributes_json_str

        # Save combined Dataset to NetCDF
        combined_ds.to_netcdf(self.combined_netcdf_file_path)

        # Save other dataset to NETCDF
        self.other.to_netcdf(self.output_dir / "other.nc")

    def read_datasets_from_netcdf(self):
        """Read datasets from a single netcdf file and populate GFPMX object attributes.

        This should be performed to restore the GFPMX object from saved scenarios.
        """
        if not self.combined_netcdf_file_path.exists():
            raise FileNotFoundError(
                f"File {self.combined_netcdf_file_path} does not exist."
            )

        # Read the combined dataset from the NetCDF file
        combined_ds = xarray.open_dataset(self.combined_netcdf_file_path)
        # Retrieve stored attributes and deserialize from JSON string
        attributes_json_str = combined_ds.attrs.get(
            "individual_dataset_attributes", "{}"
        )
        attributes_dict = json.loads(attributes_json_str)

        for product in self.products:
            # Select data corresponding to each product and drop 'product' coordinate
            ds = combined_ds.sel(product=product).drop("product")
            # Restore attributes
            ds.attrs = attributes_dict.get(product, {})
            self[product] = ds

        # Read the other dataset that doesn't have a product dimension
        self["other"] = xarray.open_dataset(self.output_dir / "other.nc")
