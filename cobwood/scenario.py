import yaml
import cobwood


def parse_scenario_yaml(scenario_name):
    """
    Parse the YAML configuration file for the given scenario name.

    Parameters:
    -----------
    scenario_name : str
        Name of the scenario

    Returns:
    --------
    dict
        Dictionary containing the configuration parameters

    For example parse the following file:

        >>> from cobwood.scenario import parse_scenario_yaml
        >>> parse_scenario_yaml("base_2021")

    """
    yaml_path = cobwood.data_dir / "scenario" / f"{scenario_name}.yaml"
    if not yaml_path.exists():
        msg = f"Configuration file not found for scenario: {scenario_name}. "
        msg += f"Expected at: {yaml_path}"
        raise FileNotFoundError(msg)
    with open(yaml_path, "r") as yaml_file:
        try:
            config = yaml.safe_load(yaml_file)
        except yaml.YAMLError as e:
            msg = f"Error parsing YAML configuration for scenario {scenario_name}: {e}"
            raise ValueError() from e
    required_fields = ["input_dir", "base_year"]
    for field in required_fields:
        if field not in config:
            msg = f"Missing required field '{field}' "
            msg += f"in configuration for scenario: {scenario_name}"
            raise ValueError(msg)
    return config
