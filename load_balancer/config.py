import json
import platform
import os

def load_config(config_path='config.json'):
    try:
        if os.path.getsize(config_path) == 0:
            raise ValueError(f"Config file '{config_path}' is empty.")
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError as e:
        print(f"Config file '{config_path}' not found.")
        raise e
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format in config file '{config_path}'.")
        raise e
    except PermissionError as e:

        op = platform.system()

        match op:
            case 'Windows':
                system_note = 'Try running the command prompt as an administrator.'
            case 'Linux' | 'Darwin':
                system_note = 'Try running the command with sudo.'
            case _:
                system_note = 'Try running the command with appropriate permissions.'

        print(f"Permission denied to access config file '{config_path}'. ({system_note})")
        raise e

    # Read port from environment variable, otherwise use config file
    port = os.environ.get('PORT')
    if port:
        config.setdefault('fastapi', {})['port'] = int(port)
    
    return config
