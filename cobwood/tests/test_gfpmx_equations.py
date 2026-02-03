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
    world_price,
    world_price_indround,
    local_price,
    forest_stock,
    compute_country_aggregates,
    compute_secondary_product_price,
    compute_one_time_step,
)


@pytest.fixture
def primary_product_dataset():
    """Create a sample primary products dataset If your goal is debugging or
    inspection (in a notebook or console), remove the @pytest.fixture decorator
    temporarily. To be able to allocate this to an actual dataset:
     ds = primary_product_dataset()
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


@pytest.fixture
def local_price_dataset():
    """Create a dataset for testing local_price with countries and world price"""
    ds = xarray.Dataset(
        {
            "price_constant": xarray.DataArray([10, 20, 30], dims=["country"]),
            "price_world_price_elasticity": xarray.DataArray(
                [0.5, 0.6, 0.7], dims=["country"]
            ),
            "price": xarray.DataArray(
                [[100, 200], [100, 200], [100, 200]],
                dims=["country", "year"],
            ),
            "c": xarray.DataArray([True, True, False], dims=["country"]),
        },
        coords={"country": ["Germany", "France", "WORLD"], "year": [1, 2]},
    )
    return ds


@pytest.fixture
def forest_stock_dataset():
    """Create a dataset for testing forest_stock"""
    ds = xarray.Dataset(
        {
            "stock": xarray.DataArray(
                [[1000, 1500], [2000, 2500]], dims=["country", "year"]
            ),
            "stock_growth_rate_without_harvest": xarray.DataArray(
                [0.02, 0.03], dims=["country"]
            ),
            "stock_harvest_effect_on_stock": xarray.DataArray(
                [0.5, 0.6], dims=["country"]
            ),
            "c": xarray.DataArray([True, True], dims=["country"]),
        },
        coords={"country": ["Germany", "France"], "year": [1, 2]},
    )
    return ds


@pytest.fixture
def indround_dataset():
    """Create a dataset for testing forest_stock with indround production"""
    ds = xarray.Dataset(
        {
            "prod": xarray.DataArray(
                [[100, 150], [200, 250]], dims=["country", "year"]
            ),
            "c": xarray.DataArray([True, True], dims=["country"]),
        },
        coords={"country": ["Germany", "France"], "year": [1, 2]},
    )
    return ds


@pytest.fixture
def fuel_dataset():
    """Create a dataset for testing forest_stock with fuel production"""
    ds = xarray.Dataset(
        {
            "prod": xarray.DataArray([[50, 75], [100, 125]], dims=["country", "year"]),
            "c": xarray.DataArray([True, True], dims=["country"]),
        },
        coords={"country": ["Germany", "France"], "year": [1, 2]},
    )
    return ds


@pytest.fixture
def country_aggregates_dataset():
    """Create a dataset for testing compute_country_aggregates with regions"""
    ds = xarray.Dataset(
        {
            "cons": xarray.DataArray(
                [
                    [100, 0],
                    [200, 0],
                    [300, 0],
                    [400, 0],
                    [0, 0],
                    [0, 0],
                    [0, 0],
                    [0, 0],
                ],
                dims=["country", "year"],
            ),
            "imp": xarray.DataArray(
                [
                    [10, 0],
                    [20, 0],
                    [30, 0],
                    [40, 0],
                    [0, 0],
                    [0, 0],
                    [0, 0],
                    [0, 0],
                ],
                dims=["country", "year"],
            ),
            "exp": xarray.DataArray(
                [
                    [5, 0],
                    [15, 0],
                    [25, 0],
                    [35, 0],
                    [0, 0],
                    [0, 0],
                    [0, 0],
                    [0, 0],
                ],
                dims=["country", "year"],
            ),
            "prod": xarray.DataArray(
                [
                    [50, 0],
                    [150, 0],
                    [250, 0],
                    [350, 0],
                    [0, 0],
                    [0, 0],
                    [0, 0],
                    [0, 0],
                ],
                dims=["country", "year"],
            ),
            "region": xarray.DataArray(
                [
                    "EUROPE",
                    "EUROPE",
                    "ASIA",
                    "NORTH AMERICA",
                    "EUROPE",
                    "ASIA",
                    "NORTH AMERICA",
                    "WORLD",
                ],
                dims=["country"],
            ),
            "c": xarray.DataArray(
                [True, True, True, True, False, False, False, False], dims=["country"]
            ),
        },
        coords={
            "country": [
                "Germany",
                "France",
                "China",
                "USA",
                "EUROPE",
                "ASIA",
                "NORTH AMERICA",
                "WORLD",
            ],
            "year": [1, 2],
        },
    )
    return ds


@pytest.fixture
def secondary_product_price_dataset():
    """Create a dataset for testing compute_secondary_product_price"""
    ds = xarray.Dataset(
        {
            "price_constant": xarray.DataArray([10, 20, 30], dims=["country"]),
            "price_input_elast": xarray.DataArray([0.4, 0.5, 0.3], dims=["country"]),
            "price_world_price_elasticity": xarray.DataArray(
                [0.4, 0.5, 0.3], dims=["country"]
            ),
            "price": xarray.DataArray(
                [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], dims=["country", "year"]
            ),
            "c": xarray.DataArray([True, True, False], dims=["country"]),
        },
        coords={"country": ["Germany", "France", "WORLD"], "year": [1, 2]},
    )
    return ds


@pytest.fixture
def primary_product_price_dataset():
    """Create a primary product dataset for testing compute_secondary_product_price"""
    ds = xarray.Dataset(
        {
            "price": xarray.DataArray([[100, 200]], dims=["country", "year"]),
        },
        coords={"country": ["WORLD"], "year": [1, 2]},
    )
    return ds


@pytest.fixture
def one_timestep_dataset():
    """Create datasets for testing compute_one_time_step"""
    countries = ["Germany", "France", "EUROPE", "WORLD"]
    years = [0, 1, 2]

    # Helper function to create a product dataset
    def create_product_ds(product_name):
        ds = xarray.Dataset(
            {
                "cons": xarray.DataArray(
                    [
                        [100.0, 0.0, 0.0],
                        [200.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                    ],
                    dims=["country", "year"],
                ),
                "imp": xarray.DataArray(
                    [
                        [10.0, 0.0, 0.0],
                        [20.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                    ],
                    dims=["country", "year"],
                ),
                "exp": xarray.DataArray(
                    [
                        [5.0, 0.0, 0.0],
                        [15.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                    ],
                    dims=["country", "year"],
                ),
                "prod": xarray.DataArray(
                    [
                        [50.0, 0.0, 0.0],
                        [150.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                    ],
                    dims=["country", "year"],
                ),
                "price": xarray.DataArray(
                    [
                        [100.0, 0.0, 0.0],
                        [100.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                        [100.0, 0.0, 0.0],
                    ],
                    dims=["country", "year"],
                ),
                "gdp": xarray.DataArray(
                    [
                        [1000.0, 1100.0, 1200.0],
                        [2000.0, 2200.0, 2400.0],
                        [0.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                    ],
                    dims=["country", "year"],
                ),
                "tariff": xarray.DataArray(
                    [
                        [0.1, 0.1, 0.1],
                        [0.2, 0.2, 0.2],
                        [0.0, 0.0, 0.0],
                        [0.0, 0.0, 0.0],
                    ],
                    dims=["country", "year"],
                ),
                "price_constant": xarray.DataArray(
                    [10.0, 20.0, 0.0, 30.0], dims=["country"]
                ),
                "price_input_elast": xarray.DataArray(
                    [0.4, 0.5, 0.0, 0.3], dims=["country"]
                ),
                "price_world_price_elasticity": xarray.DataArray(
                    [0.4, 0.5, 0.0, 0.3], dims=["country"]
                ),
                "cons_price_elasticity": xarray.DataArray(
                    [0.5, 0.6, 0.0, 0.0], dims=["country"]
                ),
                "cons_gdp_elasticity": xarray.DataArray(
                    [0.8, 0.9, 0.0, 0.0], dims=["country"]
                ),
                "imp_price_elasticity": xarray.DataArray(
                    [0.5, 0.6, 0.0, 0.0], dims=["country"]
                ),
                "imp_gdp_elasticity": xarray.DataArray(
                    [0.8, 0.9, 0.0, 0.0], dims=["country"]
                ),
                "exp_marginal_propensity_to_export": xarray.DataArray(
                    [0.1, 0.2, 0.0, 0.0], dims=["country"]
                ),
                "exp_constant": xarray.DataArray(
                    [1.0, 2.0, 0.0, 0.0], dims=["country"]
                ),
                "region": xarray.DataArray(
                    ["EUROPE", "EUROPE", "EUROPE", "WORLD"], dims=["country"]
                ),
                "c": xarray.DataArray([True, True, False, False], dims=["country"]),
                "product": product_name,
            },
            coords={"country": countries, "year": years},
        )
        return ds

    # Create datasets for primary products (pulp, indround)
    ds_pulp = create_product_ds("pulp")
    ds_pulp["cons_paper_production_elasticity"] = xarray.DataArray(
        [0.9, 1.0, 0.0, 0.0], dims=["country"]
    )
    ds_pulp["cons_products_elasticity"] = xarray.DataArray(
        [0.5, 0.6, 0.0, 0.0], dims=["country"]
    )
    ds_pulp["imp_paper_production_elasticity"] = xarray.DataArray(
        [0.9, 1.0, 0.0, 0.0], dims=["country"]
    )
    ds_pulp["imp_products_elasticity"] = xarray.DataArray(
        [0.5, 0.6, 0.0, 0.0], dims=["country"]
    )
    ds_pulp["cons_constant"] = xarray.DataArray([2.0, 3.0, 0.0, 0.0], dims=["country"])
    ds_pulp["imp_constant"] = xarray.DataArray([2.0, 3.0, 0.0, 0.0], dims=["country"])

    ds_indround = create_product_ds("indround")
    ds_indround["cons_paper_production_elasticity"] = xarray.DataArray(
        [0.9, 1.0, 0.0, 0.0], dims=["country"]
    )
    ds_indround["cons_products_elasticity"] = xarray.DataArray(
        [0.5, 0.6, 0.0, 0.0], dims=["country"]
    )
    ds_indround["imp_paper_production_elasticity"] = xarray.DataArray(
        [0.9, 1.0, 0.0, 0.0], dims=["country"]
    )
    ds_indround["imp_products_elasticity"] = xarray.DataArray(
        [0.5, 0.6, 0.0, 0.0], dims=["country"]
    )
    ds_indround["cons_constant"] = xarray.DataArray(
        [2.0, 3.0, 0.0, 0.0], dims=["country"]
    )
    ds_indround["imp_constant"] = xarray.DataArray(
        [2.0, 3.0, 0.0, 0.0], dims=["country"]
    )
    ds_indround["price_stock_elast"] = xarray.DataArray(
        [0.0, 0.0, 0.0, 0.3], dims=["country"]
    )
    ds_indround["price_trend"] = xarray.DataArray(
        [0.0, 0.0, 0.0, 0.01], dims=["country"]
    )

    # Create datasets for secondary products
    ds_sawn = create_product_ds("sawn")
    ds_sawn["cons_constant"] = xarray.DataArray([2.0, 3.0, 0.0, 0.0], dims=["country"])
    ds_sawn["imp_constant"] = xarray.DataArray([2.0, 3.0, 0.0, 0.0], dims=["country"])

    ds_panel = create_product_ds("panel")
    ds_panel["cons_constant"] = xarray.DataArray([2.0, 3.0, 0.0, 0.0], dims=["country"])
    ds_panel["imp_constant"] = xarray.DataArray([2.0, 3.0, 0.0, 0.0], dims=["country"])

    ds_fuel = create_product_ds("fuel")
    ds_fuel["cons_constant"] = xarray.DataArray([2.0, 3.0, 0.0, 0.0], dims=["country"])
    ds_fuel["imp_constant"] = xarray.DataArray([2.0, 3.0, 0.0, 0.0], dims=["country"])

    ds_paper = create_product_ds("paper")
    ds_paper["cons_constant"] = xarray.DataArray([2.0, 3.0, 0.0, 0.0], dims=["country"])
    ds_paper["imp_constant"] = xarray.DataArray([2.0, 3.0, 0.0, 0.0], dims=["country"])

    # Create other dataset for stock
    ds_other = xarray.Dataset(
        {
            "stock": xarray.DataArray(
                [
                    [1000.0, 0.0, 0.0],
                    [2000.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0],
                ],
                dims=["country", "year"],
            ),
            "stock_growth_rate_without_harvest": xarray.DataArray(
                [0.02, 0.03, 0.0, 0.0], dims=["country"]
            ),
            "stock_harvest_effect_on_stock": xarray.DataArray(
                [0.5, 0.6, 0.0, 0.0], dims=["country"]
            ),
            "region": xarray.DataArray(
                ["EUROPE", "EUROPE", "EUROPE", "WORLD"], dims=["country"]
            ),
            "c": xarray.DataArray([True, True, False, False], dims=["country"]),
        },
        coords={"country": countries, "year": years},
    )

    return {
        "ds_indround": ds_indround,
        "ds_fuel": ds_fuel,
        "ds_pulp": ds_pulp,
        "ds_sawn": ds_sawn,
        "ds_panel": ds_panel,
        "ds_paper": ds_paper,
        "ds_other": ds_other,
    }


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


def test_world_price(world_price_secondary_dataset, world_price_primary_dataset):
    """Test the world_price function"""
    ds = world_price_secondary_dataset
    ds_primary = world_price_primary_dataset
    t = 2
    # Expected: price_constant * (primary_price ^ price_input_elast)
    # = 40 * (8 ^ 0.4)
    expected_result = 40 * (8**0.4)
    result = world_price(ds, ds_primary, t)
    np.testing.assert_allclose(result.item(), expected_result)


def test_world_price_indround(indround_world_price_dataset, stock_dataset):
    """Test the world_price_indround function"""
    ds = indround_world_price_dataset
    ds_other = stock_dataset
    t = 2
    expected_result = 40 * (1000**0.5) * (5000**0.3) * np.exp(0.01 * 2)
    result = world_price_indround(ds, ds_other, t)
    np.testing.assert_allclose(result.item(), expected_result)


def test_local_price(local_price_dataset):
    """Test the local_price function"""
    ds = local_price_dataset
    t = 2
    # Expected: price_constant * (world_price ^ price_world_price_elasticity)
    # For Germany: 10 * (200 ^ 0.5) = 10 * 14.142... = 141.421...
    # For France: 20 * (200 ^ 0.6) = 20 * 21.112... = 422.247...
    # WORLD is filtered out by ds.c
    result = local_price(ds, t)
    expected_values = np.array([10 * (200**0.5), 20 * (200**0.6)])
    np.testing.assert_allclose(result.values, expected_values)


def test_forest_stock(forest_stock_dataset, indround_dataset, fuel_dataset):
    """Test the forest_stock function"""
    ds = forest_stock_dataset
    ds_indround = indround_dataset
    ds_fuel = fuel_dataset
    t = 2
    # Formula: stock[t-1] * (1 + growth_rate) - harvest_effect * (indround + fuel) / 1000
    # Germany: indround + fuel = 100 + 50 = 150
    #          stock = 1000 * 1.02 - 0.5 * 150 / 1000 = 1020 - 0.075 = 1019.925
    # France:  indround + fuel = 200 + 100 = 300
    #          stock = 2000 * 1.03 - 0.6 * 300 / 1000 = 2060 - 0.18 = 2059.82
    expected_values = np.array([1019.925, 2059.82])
    result = forest_stock(ds, ds_indround, ds_fuel, t)
    np.testing.assert_allclose(result.values, expected_values)


def test_compute_country_aggregates(country_aggregates_dataset):
    """Test the compute_country_aggregates function"""
    ds = country_aggregates_dataset
    t = 1
    # Call the function which modifies the dataset in-place
    compute_country_aggregates(ds, t)
    # Check WORLD totals (sum of Germany, France, China, USA)
    # cons: 100+200+300+400 = 1000
    # imp: 10+20+30+40 = 100
    # exp: 5+15+25+35 = 80
    # prod: 50+150+250+350 = 800
    np.testing.assert_allclose(ds["cons"].loc["WORLD", t].values, 1000)
    np.testing.assert_allclose(ds["imp"].loc["WORLD", t].values, 100)
    np.testing.assert_allclose(ds["exp"].loc["WORLD", t].values, 80)
    np.testing.assert_allclose(ds["prod"].loc["WORLD", t].values, 800)
    # Check EUROPE totals (Germany + France)
    # cons: 100+200 = 300, imp: 10+20 = 30, exp: 5+15 = 20, prod: 50+150 = 200
    np.testing.assert_allclose(ds["cons"].loc["EUROPE", t].values, 300)
    np.testing.assert_allclose(ds["imp"].loc["EUROPE", t].values, 30)
    np.testing.assert_allclose(ds["exp"].loc["EUROPE", t].values, 20)
    np.testing.assert_allclose(ds["prod"].loc["EUROPE", t].values, 200)
    # Check ASIA totals (China only)
    # cons: 300, imp: 30, exp: 25, prod: 250
    np.testing.assert_allclose(ds["cons"].loc["ASIA", t].values, 300)
    np.testing.assert_allclose(ds["imp"].loc["ASIA", t].values, 30)
    np.testing.assert_allclose(ds["exp"].loc["ASIA", t].values, 25)
    np.testing.assert_allclose(ds["prod"].loc["ASIA", t].values, 250)
    # Check NORTH AMERICA totals (USA only)
    # cons: 400, imp: 40, exp: 35, prod: 350
    np.testing.assert_allclose(ds["cons"].loc["NORTH AMERICA", t].values, 400)
    np.testing.assert_allclose(ds["imp"].loc["NORTH AMERICA", t].values, 40)
    np.testing.assert_allclose(ds["exp"].loc["NORTH AMERICA", t].values, 35)
    np.testing.assert_allclose(ds["prod"].loc["NORTH AMERICA", t].values, 350)


def test_compute_secondary_product_price(
    secondary_product_price_dataset, primary_product_price_dataset
):
    """Test the compute_secondary_product_price function"""
    ds = secondary_product_price_dataset
    ds_primary = primary_product_price_dataset
    t = 2
    # Call the function which modifies the dataset in-place
    compute_secondary_product_price(ds, ds_primary, t)
    # Check WORLD price: price_constant[WORLD] * (primary_price ^ price_input_elast[WORLD])
    # = 30 * (200 ^ 0.3)
    world_price_value = 30 * (200**0.3)
    np.testing.assert_allclose(ds["price"].loc["WORLD", t].values, world_price_value)
    # Check local prices: price_constant * (world_price ^ price_world_price_elasticity)
    # Germany: 10 * (world_price_value ^ 0.4)
    # France: 20 * (world_price_value ^ 0.5)
    expected_germany = 10 * (world_price_value**0.4)
    expected_france = 20 * (world_price_value**0.5)
    np.testing.assert_allclose(ds["price"].loc["Germany", t].values, expected_germany)
    np.testing.assert_allclose(ds["price"].loc["France", t].values, expected_france)


def test_compute_one_time_step(one_timestep_dataset):
    """Test the compute_one_time_step function"""
    datasets = one_timestep_dataset
    ds_indround = datasets["ds_indround"]
    ds_fuel = datasets["ds_fuel"]
    ds_pulp = datasets["ds_pulp"]
    ds_sawn = datasets["ds_sawn"]
    ds_panel = datasets["ds_panel"]
    ds_paper = datasets["ds_paper"]
    ds_other = datasets["ds_other"]
    year = 1

    # Call the function which modifies all datasets in-place
    compute_one_time_step(
        ds_indround, ds_fuel, ds_pulp, ds_sawn, ds_panel, ds_paper, ds_other, year
    )

    # Verify that key values have been computed and are not zero/null
    # 1. Check that stock was computed
    assert ds_other["stock"].loc["Germany", year] > 0
    assert ds_other["stock"].loc["France", year] > 0
    assert not ds_other["stock"].loc["Germany", year].isnull()

    # 2. Check that cons, imp, exp, prod were computed for secondary products
    assert ds_sawn["cons"].loc["Germany", year] > 0
    assert ds_panel["prod"].loc["France", year] >= 0
    assert not ds_fuel["imp"].loc["Germany", year].isnull()

    # 3. Check that cons, imp, exp, prod were computed for primary products
    assert ds_pulp["cons"].loc["Germany", year] > 0
    assert ds_indround["prod"].loc["France", year] >= 0

    # 4. Check that aggregates were computed
    # WORLD should be the sum of Germany and France
    world_cons_sawn = (
        ds_sawn["cons"].loc["Germany", year] + ds_sawn["cons"].loc["France", year]
    )
    np.testing.assert_allclose(
        ds_sawn["cons"].loc["WORLD", year].values, world_cons_sawn.values
    )

    # 5. Check that prices were computed
    # WORLD price for indround should not be null or zero
    assert ds_indround["price"].loc["WORLD", year] > 0
    assert not ds_indround["price"].loc["WORLD", year].isnull()
    # Local prices for indround should be computed
    assert ds_indround["price"].loc["Germany", year] > 0
    # Secondary product prices should be computed
    assert ds_sawn["price"].loc["WORLD", year] > 0
    assert ds_pulp["price"].loc["WORLD", year] > 0
    assert ds_paper["price"].loc["WORLD", year] > 0
