import json

def load_config(config_path='config.json'):
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError as e:
        print(f"Config file '{config_path}' not found.")
        raise e
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format in config file '{config_path}'.")
        raise e
    return config
