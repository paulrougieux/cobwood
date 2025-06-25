"""Run the GFPMX model and store output data

"""

from functools import cached_property
from typing import Union, List
import json
import xarray
import cobwood
import pandas

from cobwood.gfpmx_data import GFPMXData
from cobwood.gfpmx_data import compare_to_ref
from cobwood.gfpmx_data import convert_to_2d_array
from cobwood.gfpmx_data import remove_after_base_year_and_copy
from cobwood.gfpmx_equations import compute_one_time_step
from cobwood.gfpmx_plot import facet_plot_by_var
from cobwood.scenario import parse_scenario_yaml


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
        >>> gfpmxb2021 = GFPMX(input_dir="gfpmx_base2021", base_year=2021, scenario="base_2021", rerun=True)
        >>> gfpmxb2021.run_and_compare_to_ref()
        >>> gfpmxb2021.run()

    Load output data, after a run has already been completed

        >>> gfpmx_pikssp2 = GFPMX(input_dir="gfpmx_base2021", base_year=2021, scenario="pikssp2_fel1")

    You can debug data issues by creating the data object only as follows:

        >>> from cobwood.gfpmx_data import GFPMXData
        >>> gfpmx_data_b2018 = GFPMXData(data_dir="gfpmx_8_6_2021", base_year=2018)

    You can debug equations for the different model versions as follows:

        >>> from cobwood.gfpmx_equations import world_price
        >>> world_price(gfpmx_base_2018.sawn, gfpmx_base_2018.indround,2018)

    Run other base years and compare GFPMx Excel results with the one from the cobwood

        >>> # Base 2018
        >>> gfpmxb2018 = GFPMX(input_dir="gfpmx_8_6_2021", base_year=2018, scenario="base_2018")
        >>> # Run and stop when the result diverges from the reference spreadsheet
        >>> gfpmxb2018.run(compare=True)
        >>> # Run and continue when the result diverges (just print the missmatch message)
        >>> gfpmxb2018.run(compare=True, strict=False)
        >>> # Just run, without comparison (default is compare=False)
        >>> gfpmxb2021.run()
        >>> print(gfpmxb2018.indround)
        >>> # Base 2020
        >>> gfpmxb2020 = GFPMX(input_dir="gfpmx_base2020", base_year=2020, scenario="base_2020")
        >>> gfpmxb2020.run_and_compare_to_ref() # Fails
        >>> gfpmxb2021 = GFPMX(input_dir="gfpmx_base2021", base_year=2021, scenario="base_2021")

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

    def __init__(self, scenario, rerun=False):
        """
        Initialize the GFPMX model with the specified scenario.

        Parameters:
        -----------
        scenario : str
            Name of the scenario to load configuration from
        rerun : bool, optional
            Whether to rerun the model (default: False)
        """
        self.scenario = scenario
        # Parse the YAML scenario configuration file
        self.scenario_yaml_path = cobwood.data_dir / "scenario" / f"{scenario}.yaml"
        self.config = parse_scenario_yaml(self.scenario_yaml_path)
        self.input_dir = cobwood.data_dir / "gfpmx_input" / self.config["input_dir"]
        self.base_year = self.config["base_year"]
        self.output_dir = cobwood.data_dir / "gfpmx_output" / scenario
        self.plot_dir = self.output_dir / "plot"
        if not self.plot_dir.exists():
            self.plot_dir.mkdir(parents=True)
        self.combined_netcdf_file_path = self.output_dir / "combined_datasets.nc"
        self.last_time_step = 2070
        self.scenario = scenario
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
                msg += f"'{self.scenario}'.\n"
            msg += f"Load input data from {self.input_dir} and reset time series to a "
            msg += f"base year {self.base_year} before simulation start."
            print(msg)
            for product in self.products + ["other"]:
                self[product] = remove_after_base_year_and_copy(
                    self[product + "_ref"], self.base_year
                )

    @cached_property
    def input_data(self):
        """Input data"""
        return GFPMXData(self)

    def __getitem__(self, key):
        """Get a dataset from the data dictionary"""
        return getattr(self, key, None)

    def __setitem__(self, key, value):
        """Set a dataset from the data dictionary"""
        setattr(self, key, value)

    def _invalidate_cache(self):
        """Invalidate cached properties

        In case the property has not been used yet, attempting to delete it
        would raise an AttributeError: 'GFPMX' object has no attribute
        'all_products_ds'. That is why the deletion is wrapped in a try except
        statement.

        Show the impact on the all_products ds by changing roundwood production values in 2000

        >>> from cobwood.gfpmx import GFPMX
        >>> model = GFPMX(scenario="base_2021")
        >>> selector_1_prod = dict(country="France", year=2000)
        >>> selector_all_prod = dict(country="France", product="indround", year=2000)
        >>> print(model["indround"]["prod"].loc[selector_1_prod].item())
        >>> print(model.all_products_ds["prod"].loc[selector_all_prod].item())
        >>> print("When we change the product data set. Setting a value to zero.")
        >>> model["indround"]["prod"].loc[selector_1_prod] = 0
        >>> print(model["indround"]["prod"].loc[selector_1_prod].item())
        >>> print("the all_products_ds remains unchanged")
        >>> print(model.all_products_ds["prod"].loc[selector_all_prod].item())
        >>> print("Unless we clear the cache")
        >>> model._invalidate_cache()
        >>> print(model.all_products_ds["prod"].loc[selector_all_prod].item())

        """
        try:
            del self.all_products_ds
        except AttributeError:
            pass

    def run_and_compare_to_ref(self, *args, **kwargs):
        """Takes a gpfmx_data object, remove data after the base year
        run the model and compare it to the reference dataset
        """
        self.run(compare=True, *args, **kwargs)

    def run(self, compare: bool = False, rtol: float = None, strict: bool = True):
        """Run the model for many time steps from base_year + 1 to last_time_step."""
        if rtol is None:
            rtol = 1e-2
        print(f"Running {self.scenario}")
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

        # Clear the cache so that results get updated in the combined data set
        self._invalidate_cache()

        # Save simulation output
        self.write_datasets_to_netcdf()

    @cached_property
    def all_products_ds(self):
        """Combined dataset for all products

        The dataset has a third product dimension on top of the country and
        year dimensions
        Examples
        --------
        Extract industrial roundwood production data:

        >>> from cobwood.gfpmx import GFPMX
        >>> gfpmx_base_2021 = GFPMX(scenario="base_2021")
        >>> ds = gfpmx_base_2021.all_products_ds
        >>> print(ds)
        >>> print(ds.individual_dataset_attributes)

        """
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
        return combined_ds

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

        # Save the products_combined Dataset to NetCDF
        self.all_products_ds.to_netcdf(self.combined_netcdf_file_path)

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

    def facet_plot_by_var(self, product, *args, **kwargs):
        """Plot one variable for each facet for the given product

        Example use:

            >>> from cobwood.gfpmx import GFPMX
            >>> gfpmx_base2021 = GFPMX(
            ...     input_dir="gfpmx_base2021",
            ...     base_year=2021,
            ...     scenario="base_2021",
            ...     rerun=False
            ... )
            >>> gfpmxb2021.facet_plot("indround")
            >>> # The country argument can specify one line by country
            >>> gfpmxb2021.facet_plot("indround", countries=["Canada", "France", "Japan"])
            >>> # The variable argument can specify one variable by facet
            >>> gfpmxb2021.facet_plot("other", variables=["area", "stock"],
            >>>                  ylabel="Area in 1000ha and stock in million m3")

        """
        accepted_products = self.products + ["other"]
        if product not in accepted_products:
            raise ValueError(f"Product {product} not in {accepted_products}")
        g = facet_plot_by_var(self[product], *args, **kwargs)

    def get_df(
        self, product: Union[str, List[str]], var: Union[str, List[str]]
    ) -> pandas.DataFrame:
        """
        Extract time series data for given product(s) and variable(s) from a GFPMX model.

        Parameters
        ----------
        product : Union[str, List[str]]
            The product identifier(s) (e.g., "indround" for industrial roundwood,
            or ["indround", "fuel"] for multiple products).
        var : Union[str, List[str]]
            The variable identifier(s) (e.g., "prod" for production, or ["prod", "imp"]
            for multiple variables).

        Returns
        -------
        pandas.DataFrame
            DataFrame containing the time series data with reset index and renamed
            variable column(s) using the format "{product}_{var}". The scenario column
            is added as the first column.

        Examples
        --------
        Extract industrial roundwood production data:

        >>> from cobwood.gfpmx import GFPMX
        >>> gfpmx_pikssp2 = GFPMX(scenario="pikssp2")
        >>> irw_prod = gfpmx_pikssp2.get_df(product="indround", var="prod")

        Extract multiple variables for industrial roundwood:

        >>> irw = gfpmx_pikssp2.get_df(product="indround", var=["prod", "imp"])

        Extract single variable for multiple products:

        >>> irw_fw_prod = gfpmx_pikssp2.get_df(product=["indround", "fuel"], var="prod")

        Extract multiple variables for multiple products:

        >>> irw_fw_prod_imp = gfpmx_pikssp2.get_df(
        ...     product=["indround", "fuel"],
        ...     var=["prod", "imp"]
        ... )

        """
        # Convert single values to lists for uniform handling
        if isinstance(product, str):
            product = [product]
        if isinstance(var, str):
            var = [var]

        # Select the specified products from the combined dataset
        df = self.all_products_ds.sel(product=product)[var].to_dataframe().reset_index()

        # Multiple variables: create columns like indround_prod, indround_imp,
        # fuel_prod, fuel_imp
        value_vars = var
        df_melted = df.melt(
            id_vars=["country", "year", "product"],
            value_vars=value_vars,
            var_name="variable",
        )
        df_melted["product_var"] = df_melted["product"] + "_" + df_melted["variable"]
        df = df_melted.pivot_table(
            index=["country", "year"],
            columns="product_var",
            values="value",
            aggfunc="first",
        ).reset_index()
        df.columns.name = None

        # Add scenario column and move it to the front
        df["scenario"] = self.scenario
        cols = df.columns.to_list()
        cols = cols[-1:] + cols[:-1]
        df = df[cols]

        return df
