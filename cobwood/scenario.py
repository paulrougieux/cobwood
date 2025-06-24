import yaml
from pathlib import Path
from typing import Union, Dict, Any


def parse_scenario_yaml(yaml_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Parse the YAML configuration file for the given scenario.

    Parameters:
    -----------
    yaml_path : Union[str, Path]
        Path to the scenario YAML file. Can be a string or pathlib.Path object.
        If a string is provided, it will be converted to a Path object.

    Returns:
    --------
    Dict[str, Any]
        Dictionary containing the configuration parameters

    Raises:
    -------
    FileNotFoundError
        If the specified YAML file does not exist
    ValueError
        If the YAML file cannot be parsed or is missing required fields

    Examples:
    ---------
    Parse a scenario configuration file:

        >>> from cobwood.scenario import parse_scenario_yaml
        >>> from pathlib import Path
        >>> config = parse_scenario_yaml(Path.home() / "repos/cobwood_data/scenario/pikfair_fel1.yaml")

    Required fields in the YAML file:
    - input_dir: Directory containing input data
    - base_year: Base year for the scenario
    """
    # Convert string to Path object if necessary
    if not isinstance(yaml_path, Path):
        yaml_path = Path(yaml_path)

    # Check if file exists
    if not yaml_path.exists():
        msg = f"Configuration file not found at: {yaml_path}"
        raise FileNotFoundError(msg)

    # Parse YAML file
    with open(yaml_path, "r") as yaml_file:
        try:
            config = yaml.safe_load(yaml_file)
        except yaml.YAMLError as e:
            msg = f"Error parsing YAML configuration file {yaml_path}: {e}"
            raise ValueError(msg) from e

    # Validate required fields
    required_fields = ["input_dir", "base_year"]
    for field in required_fields:
        if field not in config:
            msg = f"Missing required field '{field}' in configuration file: {yaml_path}"
            raise ValueError(msg)

    return config
