import pytest
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from config import load_config

def test_valid_config():
    test_config = load_config('tests/config/test_config.json')
    threshold = test_config.get('health_checks', {}).get('threshold')
    assert threshold == 30

def test_invalid_path_config():
    with pytest.raises(FileNotFoundError):
        load_config('path/to/invalid/config.json')

def test_invalid_json_config():
    with pytest.raises(json.JSONDecodeError):
        load_config('tests/config/invalid_json.json')

def test_missing_keys_config():
    test_config = load_config('tests/config/missing_keys.json')
    assert test_config.get('dynamic_weighting', {}).get('max_cpu_usage') is None
    assert test_config.get('fastapi', {}).get('port') is None
