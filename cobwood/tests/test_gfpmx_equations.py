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
    import_demand,
    import_demand_pulp,
    # import_demand_indround,
    # export_supply   ,
    # production      ,
    # world_price     ,
    # world_price_indround   ,
    # local_price     ,
    # forest_stock    ,
)


@pytest.fixture
def primary_product_dataset():
    """Create a sample dataset for testing"""
    ds = xarray.Dataset(
        {
            "cons_constant": xarray.DataArray([2, 3, 4], dims=["country"]),
            "imp_constant": xarray.DataArray([2, 3, 4], dims=["country"]),
            "price": xarray.DataArray(
                [[1, 2], [3, 4], [5, 6]], dims=["country", "year"]
            ),
            "cons_paper_production_elasticity": xarray.DataArray(
                [0.9, 1.0, 0.8], dims=["country"]
            ),
            "cons_price_elasticity": xarray.DataArray(
                [0.5, 0.6, 0.7], dims=["country"]
            ),
            "cons_products_elasticity": xarray.DataArray(
                [0.5, 0.6, 0.7], dims=["country"]
            ),
            "tariff": xarray.DataArray(
                [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]], dims=["country", "year"]
            ),
            "c": xarray.DataArray([True, True, True], dims=["country"]),
        }
    )
    return ds


@pytest.fixture
def secondary_product_dataset():
    """Create a sample dataset for testing"""
    ds = xarray.Dataset(
        {
            "cons_constant": xarray.DataArray([2, 3, 4], dims=["country"]),
            "imp_constant": xarray.DataArray([2, 3, 4], dims=["country"]),
            "price": xarray.DataArray(
                [[1, 2], [3, 4], [5, 6]], dims=["country", "year"]
            ),
            "gdp": xarray.DataArray(
                [[100, 200], [300, 400], [500, 600]], dims=["country", "year"]
            ),
            "prod": xarray.DataArray(
                [[100, 200], [300, 400], [500, 600]], dims=["country", "year"]
            ),
            "cons_price_elasticity": xarray.DataArray(
                [0.5, 0.6, 0.7], dims=["country"]
            ),
            "imp_price_elasticity": xarray.DataArray([0.5, 0.6, 0.7], dims=["country"]),
            "cons_gdp_elasticity": xarray.DataArray([0.8, 0.9, 1.0], dims=["country"]),
            "tariff": xarray.DataArray(
                [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]], dims=["country", "year"]
            ),
            "c": xarray.DataArray([True, True, True], dims=["country"]),
        }
    )
    return ds


def test_consumption(secondary_product_dataset):
    """Test the consumption function"""
    ds = secondary_product_dataset
    t = 1
    expected_result = xarray.DataArray(
        [138.62896863, 1274.23051055, 7404.40635264], dims=["country"]
    )
    result = consumption(ds, t)
    xarray.testing.assert_allclose(result, expected_result)


def test_consumption_pulp(primary_product_dataset, secondary_product_dataset):
    """Test the consumption_pulp function"""
    ds = primary_product_dataset
    ds_paper = secondary_product_dataset
    t = 1
    expected_result = xarray.DataArray(
        [235.48160746, 2319.81845392, 2059.96572644], dims=["country"]
    )
    result = consumption_pulp(ds, ds_paper, t)
    xarray.testing.assert_allclose(result, expected_result)


def test_consumption_indround(primary_product_dataset, secondary_product_dataset):
    """Test the consumption_indround function"""
    ds = primary_product_dataset
    ds["cons_constant"].loc[2] = -10
    ds_sawn = secondary_product_dataset
    ds_panel = secondary_product_dataset
    ds_pulp = secondary_product_dataset
    t = 1
    compatible_mode = False
    expected_result = xarray.DataArray(
        [48.98979486, 408.22796795, 0],
        dims=["country"],
    )
    result = consumption_indround(ds, ds_sawn, ds_panel, ds_pulp, t, compatible_mode)
    xarray.testing.assert_allclose(result, expected_result)


def test_consumption_indround_compatible_mode(
    primary_product_dataset, secondary_product_dataset
):
    """Test the consumption_indround function with compatible mode"""
    ds = primary_product_dataset
    ds["cons_constant"].loc[2] = -10
    ds_sawn = secondary_product_dataset
    ds_panel = secondary_product_dataset
    ds_pulp = secondary_product_dataset
    t = 1
    compatible_mode = True
    expected_result = xarray.DataArray(
        [48.98979486, 408.22796795, -5860.973485],
        dims=["country"],
    )
    result = consumption_indround(ds, ds_sawn, ds_panel, ds_pulp, t, compatible_mode)
    xarray.testing.assert_allclose(result, expected_result)


def test_import_demand(secondary_product_dataset):
    """Test the import_demand function"""
    ds = secondary_product_dataset
    t = 1
    expected_result = xarray.DataArray(
        [1.043081, 2.592547, 4.999707],
        dims=["country"],
    )
    result = import_demand(ds, t)
    xarray.testing.assert_allclose(result, expected_result)


def test_import_demand_pulp(primary_product_dataset, secondary_product_dataset):
    """Test the import_demand_pulp function"""
    ds = primary_product_dataset
    ds_paper = secondary_product_dataset
    t = 1

    expected_result = xarray.DataArray(
        [1.043081, 2.592547, 2.869484],
        dims=["country"],
    )
    result = import_demand_pulp(ds, ds_paper, t)
    xarray.testing.assert_allclose(result, expected_result)
