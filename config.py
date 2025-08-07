import json

_config = json.load(open("config.json"))

def get(key, default=None):
    return _config.get(key, default=default)
