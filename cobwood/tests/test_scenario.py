"""Test scenario module functions

Run tests with:
    cd ~/rp/cobwood/
    pytest -v cobwood/tests/test_scenario.py
"""

import pytest
import yaml
from cobwood.scenario import parse_scenario_yaml


@pytest.fixture
def valid_yaml_file(tmp_path):
    """Create a valid scenario YAML file for testing"""
    yaml_file = tmp_path / "valid_scenario.yaml"
    config = {
        "input_dir": "/path/to/input",
        "base_year": 2020,
        "optional_field": "some_value",
    }
    with open(yaml_file, "w") as f:
        yaml.dump(config, f)
    return yaml_file


@pytest.fixture
def missing_field_yaml_file(tmp_path):
    """Create a YAML file missing required fields"""
    yaml_file = tmp_path / "missing_field.yaml"
    config = {
        "input_dir": "/path/to/input",
        # Missing base_year
        "optional_field": "some_value",
    }
    with open(yaml_file, "w") as f:
        yaml.dump(config, f)
    return yaml_file


@pytest.fixture
def invalid_yaml_file(tmp_path):
    """Create an invalid YAML file that cannot be parsed"""
    yaml_file = tmp_path / "invalid.yaml"
    with open(yaml_file, "w") as f:
        f.write("invalid: yaml: content:\n  - badly: [formatted\n    missing: bracket")
    return yaml_file


def test_parse_valid_yaml_with_path_object(valid_yaml_file):
    """Test parsing a valid YAML file using a Path object"""
    config = parse_scenario_yaml(valid_yaml_file)

    # Verify required fields are present
    assert "input_dir" in config
    assert "base_year" in config

    # Verify values
    assert config["input_dir"] == "/path/to/input"
    assert config["base_year"] == 2020
    assert config["optional_field"] == "some_value"


def test_parse_valid_yaml_with_string_path(valid_yaml_file):
    """Test parsing a valid YAML file using a string path"""
    config = parse_scenario_yaml(str(valid_yaml_file))

    # Verify required fields are present
    assert "input_dir" in config
    assert "base_year" in config

    # Verify values
    assert config["input_dir"] == "/path/to/input"
    assert config["base_year"] == 2020


def test_parse_yaml_file_not_found(tmp_path):
    """Test that FileNotFoundError is raised when file doesn't exist"""
    nonexistent_file = tmp_path / "nonexistent.yaml"

    with pytest.raises(FileNotFoundError) as exc_info:
        parse_scenario_yaml(nonexistent_file)

    assert str(nonexistent_file) in str(exc_info.value)


def test_parse_yaml_missing_input_dir(tmp_path):
    """Test that ValueError is raised when input_dir field is missing"""
    yaml_file = tmp_path / "missing_input_dir.yaml"
    config = {"base_year": 2020, "optional_field": "some_value"}
    with open(yaml_file, "w") as f:
        yaml.dump(config, f)

    with pytest.raises(ValueError) as exc_info:
        parse_scenario_yaml(yaml_file)

    assert "input_dir" in str(exc_info.value)
    assert "Missing required field" in str(exc_info.value)


def test_parse_yaml_missing_base_year(missing_field_yaml_file):
    """Test that ValueError is raised when base_year field is missing"""
    with pytest.raises(ValueError) as exc_info:
        parse_scenario_yaml(missing_field_yaml_file)

    assert "base_year" in str(exc_info.value)
    assert "Missing required field" in str(exc_info.value)


def test_parse_invalid_yaml_syntax(invalid_yaml_file):
    """Test that ValueError is raised when YAML syntax is invalid"""
    with pytest.raises(ValueError) as exc_info:
        parse_scenario_yaml(invalid_yaml_file)

    assert "Error parsing YAML" in str(exc_info.value)


def test_parse_yaml_with_all_required_fields_only(tmp_path):
    """Test parsing a YAML file with only required fields"""
    yaml_file = tmp_path / "minimal.yaml"
    config = {"input_dir": "/minimal/path", "base_year": 2015}
    with open(yaml_file, "w") as f:
        yaml.dump(config, f)

    result = parse_scenario_yaml(yaml_file)

    assert len(result) == 2
    assert result["input_dir"] == "/minimal/path"
    assert result["base_year"] == 2015


def test_parse_yaml_with_additional_fields(tmp_path):
    """Test parsing a YAML file with additional optional fields"""
    yaml_file = tmp_path / "extended.yaml"
    config = {
        "input_dir": "/extended/path",
        "base_year": 2025,
        "scenario_name": "test_scenario",
        "parameters": {"growth_rate": 0.05, "inflation": 0.02},
        "regions": ["EU", "USA", "China"],
    }
    with open(yaml_file, "w") as f:
        yaml.dump(config, f)

    result = parse_scenario_yaml(yaml_file)

    # Verify required fields
    assert result["input_dir"] == "/extended/path"
    assert result["base_year"] == 2025

    # Verify additional fields are preserved
    assert result["scenario_name"] == "test_scenario"
    assert result["parameters"]["growth_rate"] == 0.05
    assert result["regions"] == ["EU", "USA", "China"]


def test_parse_yaml_empty_file(tmp_path):
    """Test that TypeError is raised when YAML file is empty (yaml.safe_load returns None)"""
    yaml_file = tmp_path / "empty.yaml"
    yaml_file.touch()  # Create empty file

    # Empty YAML files cause yaml.safe_load to return None, which results in TypeError
    # when checking if fields are in the config
    with pytest.raises(TypeError):
        parse_scenario_yaml(yaml_file)
