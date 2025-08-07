import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from load_balancer.algorithms.base import ServerMetrics


def test_server_metrics_is_stale():
    server_metrics = ServerMetrics()
    assert server_metrics.is_stale() == False


def test_server_metrics_is_stale_with_old_timestamp():
    import time
    old_time = time.time() - 3600  # 1 hour ago
    server_metrics = ServerMetrics(last_updated=old_time)
    assert server_metrics.is_stale() == True


def test_server_metrics_is_stale_with_custom_threshold():
    import time
    old_time = time.time() - 10
    server_metrics = ServerMetrics(last_updated=old_time)
    assert server_metrics.is_stale() == False
    assert server_metrics.is_stale(threshold=5.0) == True
