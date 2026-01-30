"""Run tests with

cd ~/repos/cobwood/
pytest -v

"""

# Pylint exception needed https://github.com/pylint-dev/pylint/issues/6531
# pylint: disable=redefined-outer-name
import pytest
import xarray
import numpy as np
from cobwood.gfpmx_equations import (
    consumption,
    consumption_pulp,
    consumption_indround,
    import_demand,
    import_demand_pulp,
    import_demand_indround,
    export_supply,
    production,
    # world_price,
    world_price_indround,
    # local_price,
    # forest_stock,
)


@pytest.fixture
def primary_product_dataset():
    """Create a sample primary products dataset If your goal is debugging or
    inspection (in a notebook or console), remove the @pytest.fixture decorator
    temporarily. To be able to allocate this to an actual dataset:
    >>> ds = primary_product_dataset()
    """
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
            "imp_price_elasticity": xarray.DataArray([0.5, 0.6, 0.7], dims=["country"]),
            "imp_products_elasticity": xarray.DataArray(
                [0.5, 0.6, 0.7], dims=["country"]
            ),
            "imp_paper_production_elasticity": xarray.DataArray(
                [0.9, 1.0, 0.8], dims=["country"]
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
            "imp_gdp_elasticity": xarray.DataArray([0.8, 0.9, 1.0], dims=["country"]),
            "tariff": xarray.DataArray(
                [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]], dims=["country", "year"]
            ),
            "imp": xarray.DataArray(
                [[10, 20], [30, 40], [50, 60]], dims=["country", "year"]
            ),
            "cons": xarray.DataArray(
                [[100, 200], [300, 400], [500, 600]], dims=["country", "year"]
            ),
            "exp": xarray.DataArray(
                [[10, 20], [30, 40], [50, 60]], dims=["country", "year"]
            ),
            "exp_marginal_propensity_to_export": xarray.DataArray(
                [0.1, 0.2, 0.3], dims=["country"]
            ),
            "exp_constant": xarray.DataArray([1, 2, 3], dims=["country"]),
            "c": xarray.DataArray([True, True, True], dims=["country"]),
        }
    )
    return ds


@pytest.fixture
def world_price_primary_dataset():
    """Create a minimal dataset for testing world_price with primary products"""
    ds = xarray.Dataset(
        {
            "price": xarray.DataArray([[7, 8]], dims=["country", "year"]),
        },
        coords={"country": ["WORLD"], "year": [1, 2]},
    )
    return ds


@pytest.fixture
def indround_world_price_dataset():
    """Create a minimal dataset for testing world_price_indround with indround products"""
    ds = xarray.Dataset(
        {
            "price_constant": xarray.DataArray([40], dims=["country"]),
            "price_world_price_elasticity": xarray.DataArray([0.5], dims=["country"]),
            "price_stock_elast": xarray.DataArray([0.3], dims=["country"]),
            "price_trend": xarray.DataArray([0.01], dims=["country"]),
            "prod": xarray.DataArray([[100, 1000]], dims=["country", "year"]),
        },
        coords={"country": ["WORLD"], "year": [1, 2]},
    )
    return ds


@pytest.fixture
def stock_dataset():
    """Create a minimal dataset for testing world_price_indround with stock"""
    ds = xarray.Dataset(
        {
            "stock": xarray.DataArray([[1000, 5000]], dims=["country", "year"]),
        },
        coords={"country": ["WORLD"], "year": [1, 2]},
    )
    return ds


@pytest.fixture
def world_price_secondary_dataset():
    """Create a minimal dataset for testing world_price with secondary products"""
    ds = xarray.Dataset(
        {
            "price_constant": xarray.DataArray([40], dims=["country"]),
            "price_input_elast": xarray.DataArray([0.4], dims=["country"]),
        },
        coords={"country": ["WORLD"]},
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
        [145.395289, 1491.468245, 9834.541699],
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
        [246.975193, 2715.313696, 2736.049032],
        dims=["country"],
    )
    result = import_demand_pulp(ds, ds_paper, t)
    xarray.testing.assert_allclose(result, expected_result)


def test_import_demand_indround(primary_product_dataset, secondary_product_dataset):
    """Test the import_demand_indround function"""
    ds = primary_product_dataset
    ds["imp_constant"].loc[2] = -10
    ds_sawn = secondary_product_dataset
    ds_panel = secondary_product_dataset
    ds_pulp = secondary_product_dataset
    t = 1
    compatible_mode = False
    expected_result = xarray.DataArray(
        [53.665631, 499.550705, 0],
        dims=["country"],
    )
    result = import_demand_indround(ds, ds_sawn, ds_panel, ds_pulp, t, compatible_mode)
    xarray.testing.assert_allclose(result, expected_result)


def test_export_supply(secondary_product_dataset):
    """Test the export_supply function"""
    ds = secondary_product_dataset
    t = 1
    expected_result = xarray.DataArray([13, 26, 39], dims=["country"])
    result = export_supply(ds, t)
    xarray.testing.assert_allclose(result, expected_result)


def test_production(secondary_product_dataset):
    """Test the production function"""
    ds = secondary_product_dataset
    t = 1
    expected_result = xarray.DataArray([200, 400, 600], dims=["country"])
    result = production(ds, t)
    xarray.testing.assert_allclose(result, expected_result)


def test_world_price_indround(indround_world_price_dataset, stock_dataset):
    """Test the world_price_indround function"""
    ds = indround_world_price_dataset
    ds_other = stock_dataset
    t = 2
    expected_result = 40 * (1000**0.5) * (5000**0.3) * np.exp(0.01 * 2)
    result = world_price_indround(ds, ds_other, t)
    np.testing.assert_allclose(result.item(), expected_result)
