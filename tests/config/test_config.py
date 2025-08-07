import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from config import load_config

def test_valid_config():
    test_config = load_config('tests/config/test_config.json')
    threshold = test_config.get('health_checks').get('threshold')
    assert threshold == 30
