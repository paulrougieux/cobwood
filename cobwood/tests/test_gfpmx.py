"""Test GFPMX class methods for NetCDF I/O operations

Run tests with:
    cd ~/rp/cobwood/
    pytest -v cobwood/tests/test_gfpmx.py
"""

import pytest
import xarray
import json
from cobwood.gfpmx import GFPMX


@pytest.fixture
def mock_gfpmx(tmp_path):
    """Create a mock GFPMX object with minimal setup for testing I/O methods"""
    # Use pytest's tmp_path fixture
    output_dir = tmp_path / "test_output"

    # Create a simple class to hold our mock data
    class MockGFPMX:
        def __init__(self):
            self.output_dir = output_dir
            self.combined_netcdf_file_path = self.output_dir / "combined_datasets.nc"
            self.products = ["indround", "fuel", "sawn", "panel", "pulp", "paper"]

            # Create sample datasets for each product
            countries = ["Germany", "France", "USA"]
            years = [2020, 2021, 2022]

            for product in self.products:
                ds = xarray.Dataset(
                    {
                        "cons": xarray.DataArray(
                            [[100, 110, 120], [200, 210, 220], [300, 310, 320]],
                            dims=["country", "year"],
                        ),
                        "prod": xarray.DataArray(
                            [[50, 55, 60], [150, 155, 160], [250, 255, 260]],
                            dims=["country", "year"],
                        ),
                        "imp": xarray.DataArray(
                            [[10, 11, 12], [20, 21, 22], [30, 31, 32]],
                            dims=["country", "year"],
                        ),
                        "exp": xarray.DataArray(
                            [[5, 6, 7], [15, 16, 17], [25, 26, 27]],
                            dims=["country", "year"],
                        ),
                        "price": xarray.DataArray(
                            [[100, 105, 110], [100, 105, 110], [100, 105, 110]],
                            dims=["country", "year"],
                        ),
                    },
                    coords={"country": countries, "year": years},
                    attrs={
                        "product_name": product,
                        "description": f"Test dataset for {product}",
                    },
                )
                setattr(self, product, ds)

            # Create 'other' dataset
            self.other = xarray.Dataset(
                {
                    "stock": xarray.DataArray(
                        [[1000, 1100, 1200], [2000, 2100, 2200], [3000, 3100, 3200]],
                        dims=["country", "year"],
                    ),
                },
                coords={"country": countries, "year": years},
                attrs={"description": "Forest stock data"},
            )

        def __getitem__(self, key):
            return getattr(self, key, None)

        def __setitem__(self, key, value):
            setattr(self, key, value)

        @property
        def all_products_ds(self):
            """Create combined dataset for all products"""
            datasets_to_combine = []
            attributes_dict = {}

            for product in self.products:
                ds = self[product].assign_coords(product=product)
                ds = ds.expand_dims("product")
                datasets_to_combine.append(ds)
                attributes_dict[product] = ds.attrs

            combined_ds = xarray.concat(datasets_to_combine, dim="product")
            attributes_json_str = json.dumps(attributes_dict)
            combined_ds.attrs["individual_dataset_attributes"] = attributes_json_str
            return combined_ds

        # Bind the actual methods we want to test
        def write_datasets_to_netcdf(self):
            return GFPMX.write_datasets_to_netcdf(self)

        def read_datasets_from_netcdf(self):
            return GFPMX.read_datasets_from_netcdf(self)

    return MockGFPMX()


def test_write_datasets_to_netcdf(mock_gfpmx):
    """Test writing datasets to NetCDF files"""
    # Write datasets to NetCDF
    mock_gfpmx.write_datasets_to_netcdf()

    # Verify that the output directory was created
    assert mock_gfpmx.output_dir.exists()

    # Verify that the combined NetCDF file was created
    assert mock_gfpmx.combined_netcdf_file_path.exists()

    # Verify that the 'other' NetCDF file was created
    other_file = mock_gfpmx.output_dir / "other.nc"
    assert other_file.exists()

    # Read back the combined dataset and verify structure
    combined_ds = xarray.open_dataset(mock_gfpmx.combined_netcdf_file_path)

    # Check that it has the product dimension
    assert "product" in combined_ds.dims
    assert len(combined_ds.product) == len(mock_gfpmx.products)

    # Check that it has the expected data variables
    assert "cons" in combined_ds.data_vars
    assert "prod" in combined_ds.data_vars
    assert "imp" in combined_ds.data_vars
    assert "exp" in combined_ds.data_vars
    assert "price" in combined_ds.data_vars

    # Check that attributes were preserved
    assert "individual_dataset_attributes" in combined_ds.attrs
    attributes_dict = json.loads(combined_ds.attrs["individual_dataset_attributes"])
    assert len(attributes_dict) == len(mock_gfpmx.products)

    # Verify data for a specific product
    indround_data = combined_ds.sel(product="indround").drop_vars("product")
    expected_cons = mock_gfpmx["indround"]["cons"]
    xarray.testing.assert_allclose(indround_data["cons"], expected_cons)

    # Read back the 'other' dataset
    other_ds = xarray.open_dataset(other_file)
    assert "stock" in other_ds.data_vars
    xarray.testing.assert_allclose(other_ds["stock"], mock_gfpmx.other["stock"])

    combined_ds.close()
    other_ds.close()


def test_read_datasets_from_netcdf(mock_gfpmx):
    """Test reading datasets from NetCDF files"""
    # First write the datasets
    mock_gfpmx.write_datasets_to_netcdf()

    # Store original data for comparison
    original_data = {}
    for product in mock_gfpmx.products:
        original_data[product] = mock_gfpmx[product].copy(deep=True)
    original_other = mock_gfpmx.other.copy(deep=True)

    # Clear the datasets to simulate loading from scratch
    for product in mock_gfpmx.products:
        setattr(mock_gfpmx, product, None)
    mock_gfpmx.other = None

    # Now read them back
    mock_gfpmx.read_datasets_from_netcdf()

    # Verify that all product datasets were loaded
    for product in mock_gfpmx.products:
        assert mock_gfpmx[product] is not None
        assert isinstance(mock_gfpmx[product], xarray.Dataset)

        # Verify the data matches the original
        xarray.testing.assert_allclose(
            mock_gfpmx[product]["cons"], original_data[product]["cons"]
        )
        xarray.testing.assert_allclose(
            mock_gfpmx[product]["prod"], original_data[product]["prod"]
        )

        # Verify attributes were restored
        assert mock_gfpmx[product].attrs == original_data[product].attrs

    # Verify 'other' dataset was loaded
    assert mock_gfpmx.other is not None
    xarray.testing.assert_allclose(mock_gfpmx.other["stock"], original_other["stock"])


def test_read_datasets_from_netcdf_file_not_found(mock_gfpmx):
    """Test that read_datasets_from_netcdf raises FileNotFoundError when file doesn't exist"""
    # Ensure the file doesn't exist
    if mock_gfpmx.combined_netcdf_file_path.exists():
        mock_gfpmx.combined_netcdf_file_path.unlink()

    # Should raise FileNotFoundError
    with pytest.raises(FileNotFoundError) as exc_info:
        mock_gfpmx.read_datasets_from_netcdf()

    assert str(mock_gfpmx.combined_netcdf_file_path) in str(exc_info.value)


def test_write_read_roundtrip(mock_gfpmx):
    """Test complete roundtrip: write and then read datasets"""
    # Store original datasets
    original_datasets = {}
    for product in mock_gfpmx.products:
        original_datasets[product] = mock_gfpmx[product].copy(deep=True)
    original_other = mock_gfpmx.other.copy(deep=True)

    # Write to NetCDF
    mock_gfpmx.write_datasets_to_netcdf()

    # Modify datasets in memory (simulate clearing)
    for product in mock_gfpmx.products:
        mock_gfpmx[product] = None
    mock_gfpmx.other = None

    # Read back from NetCDF
    mock_gfpmx.read_datasets_from_netcdf()

    # Verify all data matches original
    for product in mock_gfpmx.products:
        for var in ["cons", "prod", "imp", "exp", "price"]:
            xarray.testing.assert_allclose(
                mock_gfpmx[product][var],
                original_datasets[product][var],
                rtol=1e-10,
            )
        # Verify attributes
        assert mock_gfpmx[product].attrs == original_datasets[product].attrs

    # Verify 'other' dataset
    xarray.testing.assert_allclose(
        mock_gfpmx.other["stock"], original_other["stock"], rtol=1e-10
    )
    assert mock_gfpmx.other.attrs == original_other.attrs


def test_combined_dataset_structure(mock_gfpmx):
    """Test that the combined dataset has the correct structure"""
    # Write datasets
    mock_gfpmx.write_datasets_to_netcdf()

    # Load and inspect the combined dataset
    combined_ds = xarray.open_dataset(mock_gfpmx.combined_netcdf_file_path)

    # Check dimensions
    assert "country" in combined_ds.dims
    assert "year" in combined_ds.dims
    assert "product" in combined_ds.dims

    # Check coordinates
    assert list(combined_ds.product.values) == mock_gfpmx.products

    # Check that individual product attributes are stored
    attributes_json_str = combined_ds.attrs["individual_dataset_attributes"]
    attributes_dict = json.loads(attributes_json_str)

    for product in mock_gfpmx.products:
        assert product in attributes_dict
        assert attributes_dict[product]["product_name"] == product

    combined_ds.close()
