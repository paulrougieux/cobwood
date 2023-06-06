""" Run tests with

    cd ~/repos/cobwood/
    pytest

"""

# Pylint exception needed https://github.com/pylint-dev/pylint/issues/6531
# pylint: disable=redefined-outer-name
import pytest
import xarray
from cobwood.gfpmx_equations import (
    consumption,
    consumption_pulp,
    consumption_indround,
)


@pytest.fixture
def primary_product_dataset():
    """Create a sample dataset for testing"""
    ds = xarray.Dataset(
        {
            "cons_constant": xarray.DataArray([2, 3, 4], dims=["c"]),
            "price": xarray.DataArray([[1, 2], [3, 4], [5, 6]], dims=["c", "t"]),
            "cons_paper_production_elasticity": xarray.DataArray(
                [0.9, 1.0, 0.8], dims=["c"]
            ),
            "cons_price_elasticity": xarray.DataArray([0.5, 0.6, 0.7], dims=["c"]),
            "cons_products_elasticity": xarray.DataArray([0.5, 0.6, 0.7], dims=["c"]),
        }
    )
    return ds


@pytest.fixture
def secondary_product_dataset():
    """Create a sample dataset for testing"""
    ds = xarray.Dataset(
        {
            "cons_constant": xarray.DataArray([2, 3, 4], dims=["c"]),
            "price": xarray.DataArray([[1, 2], [3, 4], [5, 6]], dims=["c", "t"]),
            "gdp": xarray.DataArray(
                [[100, 200], [300, 400], [500, 600]], dims=["c", "t"]
            ),
            "prod": xarray.DataArray(
                [[100, 200], [300, 400], [500, 600]], dims=["c", "t"]
            ),
            "cons_price_elasticity": xarray.DataArray([0.5, 0.6, 0.7], dims=["c"]),
            "cons_gdp_elasticity": xarray.DataArray([0.8, 0.9, 1.0], dims=["c"]),
        }
    )
    return ds


def test_consumption(secondary_product_dataset):
    """Test the consumption function"""
    ds = secondary_product_dataset
    t = 1
    expected_result = xarray.DataArray(
        [138.62896863, 1274.23051055, 7404.40635264], dims=["c"]
    )
    result = consumption(ds, t)
    xarray.testing.assert_allclose(result, expected_result)


def test_consumption_pulp(primary_product_dataset, secondary_product_dataset):
    """Test the consumption_pulp function"""
    ds = primary_product_dataset
    ds_paper = secondary_product_dataset
    t = 1
    expected_result = xarray.DataArray(
        [235.48160746, 2319.81845392, 2059.96572644], dims=["c"]
    )
    result = consumption_pulp(ds, ds_paper, t)
    xarray.testing.assert_allclose(result, expected_result)


def test_consumption_indround(primary_product_dataset, secondary_product_dataset):
    """Test the consumption_indround function"""
    ds = primary_product_dataset
    ds_sawn = secondary_product_dataset
    ds_panel = secondary_product_dataset
    ds_pulp = secondary_product_dataset
    t = 1
    compatible_mode = False
    expected_result = xarray.DataArray(
        [48.98979486, 408.22796795, 2344.38939382],
        dims=["c"],
    )
    result = consumption_indround(ds, ds_sawn, ds_panel, ds_pulp, t, compatible_mode)
    xarray.testing.assert_allclose(result, expected_result)


def test_consumption_indround_compatible_mode(
    primary_product_dataset, secondary_product_dataset
):
    """Test the consumption_indround function with compatible mode"""
    ds = primary_product_dataset
    ds_sawn = secondary_product_dataset
    ds_panel = secondary_product_dataset
    ds_pulp = secondary_product_dataset
    t = 1
    compatible_mode = True
    expected_result = xarray.DataArray(
        [48.98979486, 408.22796795, 2344.38939382],
        dims=["c"],
    )
    result = consumption_indround(ds, ds_sawn, ds_panel, ds_pulp, t, compatible_mode)
    xarray.testing.assert_allclose(result, expected_result)
