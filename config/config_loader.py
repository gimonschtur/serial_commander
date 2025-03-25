import json
import os
from typing import Dict  # Import Dict for type hinting

def load_config(config_file: str) -> Dict:
    """Load the configuration from the config_file file.

    Args:
        config_file (str): The path to the configuration file.

    Returns:
        Dict: A dictionary containing the configuration data.

    Raises:
        FileNotFoundError: If the config file doesn't exist
        json.JSONDecodeError: If the config file is not valid JSON
    """
    config_path = os.path.join(os.path.dirname(__file__), config_file)

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in config file: {config_path}", e.doc, e.pos)

def load_esp32config() -> Dict:
    """Load and validate ESP32 configuration.

    Returns:
        Dict: Validated configuration

    Raises:
        ValueError: If required configuration fields are missing
    """
    config = load_config('esp32_config.json')

    required_fields = ['ESP32_UART_CONFIG', 'ESP32_RESPONSE_PATTERNS']
    missing_fields = [field for field in required_fields if field not in config]

    if missing_fields:
        raise ValueError(f"Missing required configuration fields: {missing_fields}")

    return config
