import pytest
import time
import threading
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

from load_balancer.algorithms.round_robin import RoundRobin
from load_balancer.algorithms.base import Server, ServerStatus, LoadBalancingContext


class TestRoundRobinIntegration:
    """Integration and performance tests for the Round Robin load balancing algorithm."""

    @pytest.fixture
    def large_server_pool(self):
        """Create a large pool of servers for performance testing."""
        servers = []
        for i in range(50):
            server = Server(
                id=f"server_{i:02d}",
                address=f"192.168.{i // 10}.{i % 10}",
                port=8080 + i,
                weight=1.0
            )
            servers.append(server)
        return servers

    @pytest.fixture
    def round_robin_with_servers(self, large_server_pool):
        """Create a RoundRobin instance with a large server pool."""
        rr = RoundRobin()
        for server in large_server_pool[:10]:  # Use first 10 servers
            rr.add_server(server)
        return rr

    def test_distribution_fairness(self, round_robin_with_servers):
        """Test that requests are distributed fairly across servers."""
        selections = []
        num_requests = 1000

        for _ in range(num_requests):
            selected = round_robin_with_servers.select_server()
            selections.append(selected.id)

        selection_counts = Counter(selections)

        expected_per_server = num_requests // 10
        tolerance = expected_per_server * 0.1  # 10% tolerance

        for server_id, count in selection_counts.items():
            assert abs(count - expected_per_server) <= tolerance, \
                f"Server {server_id} got {count} requests, expected ~{expected_per_server}"

        assert len(selection_counts) == 10

    def test_round_robin_pattern_verification(self, round_robin_with_servers):
        """Verify the exact round-robin pattern over multiple cycles."""
        expected_pattern = [f"server_{i:02d}" for i in range(10)]
        actual_selections = []

        for _ in range(30):
            selected = round_robin_with_servers.select_server()
            actual_selections.append(selected.id)

        for cycle in range(3):
            start_idx = cycle * 10
            end_idx = start_idx + 10
            cycle_selections = actual_selections[start_idx:end_idx]
            assert cycle_selections == expected_pattern, \
                f"Cycle {cycle + 1} pattern mismatch: {cycle_selections}"

    def test_high_concurrency_performance(self, round_robin_with_servers):
        """Test performance under high concurrent load."""
        num_threads = 20
        selections_per_thread = 100
        total_selections = num_threads * selections_per_thread

        results = []
        start_time = time.time()

        def make_selections():
            thread_results = []
            for _ in range(selections_per_thread):
                selected = round_robin_with_servers.select_server()
                thread_results.append(selected.id)
            return thread_results

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_selections) for _ in range(num_threads)]

            for future in as_completed(futures):
                results.extend(future.result())

        end_time = time.time()
        duration = end_time - start_time

        assert len(results) == total_selections

        selections_per_second = total_selections / duration
        print(f"Performance: {selections_per_second:.2f} selections/second")

        assert selections_per_second > 10000, \
            f"Performance too slow: {selections_per_second:.2f} selections/second"

        selection_counts = Counter(results)
        expected_per_server = total_selections // 10
        tolerance = expected_per_server * 0.2  # 20% tolerance for concurrent access

        for server_id, count in selection_counts.items():
            assert abs(count - expected_per_server) <= tolerance, \
                f"Concurrent distribution unfair for {server_id}: {count} vs ~{expected_per_server}"

    def test_dynamic_server_management_during_load(self, large_server_pool):
        """Test adding/removing servers while under load."""
        rr = RoundRobin()

        initial_servers = large_server_pool[:5]
        for server in initial_servers:
            rr.add_server(server)

        selections = []
        management_events = []

        def selection_worker():
            """Continuously make selections."""
            for _ in range(200):
                try:
                    selected = rr.select_server()
                    selections.append((time.time(), selected.id))
                    time.sleep(0.001)  # Small delay
                except Exception as e:
                    selections.append((time.time(), f"ERROR: {e}"))

        def management_worker():
            """Add and remove servers during selections."""
            time.sleep(0.1)  # Let selection start

            for i in range(5, 8):
                rr.add_server(large_server_pool[i])
                management_events.append(('ADD', large_server_pool[i].id))
                time.sleep(0.05)

            time.sleep(0.1)

            for i in range(2):
                rr.remove_server(f"server_{i:02d}")
                management_events.append(('REMOVE', f"server_{i:02d}"))
                time.sleep(0.05)

        selection_thread = threading.Thread(target=selection_worker)
        management_thread = threading.Thread(target=management_worker)

        selection_thread.start()
        management_thread.start()

        selection_thread.join()
        management_thread.join()

        errors = [s for s in selections if isinstance(s[1], str) and s[1].startswith("ERROR")]
        assert len(errors) == 0, f"Errors occurred during dynamic management: {errors}"

        selected_servers = set(s[1] for s in selections if not s[1].startswith("ERROR"))
        assert len(selected_servers) > 5, "Should have selections from added servers"

    def test_health_status_transitions_under_load(self, round_robin_with_servers):
        """Test server health status changes during continuous load."""
        selections = defaultdict(list)
        health_changes = []

        def selection_worker():
            """Make continuous selections."""
            for _ in range(300):
                try:
                    selected = round_robin_with_servers.select_server()
                    selections[selected.id].append(time.time())
                    time.sleep(0.002)
                except Exception as e:
                    selections['ERROR'].append((time.time(), str(e)))

        def health_manager():
            """Change server health status during selections."""
            time.sleep(0.1)

            unhealthy_servers = ['server_02', 'server_05', 'server_07']
            for server_id in unhealthy_servers:
                round_robin_with_servers.update_server_status(server_id, ServerStatus.UNHEALTHY)
                health_changes.append(('UNHEALTHY', server_id))
                time.sleep(0.1)

            time.sleep(0.2)

            for server_id in unhealthy_servers[:2]:
                round_robin_with_servers.update_server_status(server_id, ServerStatus.HEALTHY)
                health_changes.append(('HEALTHY', server_id))
                time.sleep(0.1)

        selection_thread = threading.Thread(target=selection_worker)
        health_thread = threading.Thread(target=health_manager)

        selection_thread.start()
        health_thread.start()

        selection_thread.join()
        health_thread.join()

        assert 'ERROR' not in selections, f"Errors during health transitions: {selections.get('ERROR', [])}"

        server_07_selections = len(selections.get('server_07', []))
        healthy_server_selections = len(selections.get('server_01', []))

        assert server_07_selections < healthy_server_selections * 0.8, \
            "Unhealthy server was selected too frequently"

    def test_load_balancing_with_context(self, round_robin_with_servers):
        """Test that LoadBalancingContext doesn't affect round-robin order."""
        contexts = [
            LoadBalancingContext(client_ip=f"192.168.1.{i}", request_path=f"/api/endpoint_{i}")
            for i in range(1, 21)
        ]

        selections_with_context = []
        selections_without_context = []

        for context in contexts:
            selected = round_robin_with_servers.select_server(context)
            selections_with_context.append(selected.id)

        round_robin_with_servers.current_server_index = 0
        for _ in range(20):
            selected = round_robin_with_servers.select_server()
            selections_without_context.append(selected.id)

        assert selections_with_context == selections_without_context, \
            "Context should not affect round-robin selection order"

    def test_memory_usage_stability(self, large_server_pool):
        """Test that memory usage remains stable under continuous operation."""
        import tracemalloc

        tracemalloc.start()
        rr = RoundRobin()

        for server in large_server_pool[:10]:
            rr.add_server(server)

        initial_snapshot = tracemalloc.take_snapshot()

        for cycle in range(100):
            for _ in range(100):
                rr.select_server()

            server_to_change = f"server_{cycle % 10:02d}"
            rr.update_server_status(server_to_change, ServerStatus.MAINTENANCE)
            rr.update_server_status(server_to_change, ServerStatus.HEALTHY)

            rr.update_server_metrics(
                server_to_change,
                response_time=0.1 + (cycle % 10) * 0.01,
                cpu_usage=0.5 + (cycle % 10) * 0.05
            )

        final_snapshot = tracemalloc.take_snapshot()
        top_stats = final_snapshot.compare_to(initial_snapshot, 'lineno')

        total_growth = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)
        assert total_growth < 1024 * 1024, f"Memory growth too high: {total_growth} bytes"

        tracemalloc.stop()

    def test_statistics_accuracy_under_load(self, round_robin_with_servers):
        """Test that statistics remain accurate under concurrent load."""
        num_threads = 10
        selections_per_thread = 100

        def make_selections():
            for _ in range(selections_per_thread):
                round_robin_with_servers.select_server()

        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=make_selections)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        stats = round_robin_with_servers.get_statistics()
        expected_total = num_threads * selections_per_thread

        assert stats['total_requests'] == expected_total
        assert stats['successful_selections'] == expected_total
        assert stats['failed_selections'] == 0
        assert stats['success_rate'] == 1.0

    def test_extreme_load_stability(self, round_robin_with_servers):
        """Test stability under extreme concurrent load."""
        num_threads = 50
        selections_per_thread = 50
        total_expected = num_threads * selections_per_thread

        successful_selections = []
        errors = []

        def extreme_load_worker():
            thread_selections = []
            thread_errors = []

            for _ in range(selections_per_thread):
                try:
                    selected = round_robin_with_servers.select_server()
                    thread_selections.append(selected.id)
                except Exception as e:
                    thread_errors.append(str(e))

            return thread_selections, thread_errors

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(extreme_load_worker) for _ in range(num_threads)]

            for future in as_completed(futures):
                selections, errs = future.result()
                successful_selections.extend(selections)
                errors.extend(errs)

        end_time = time.time()

        assert len(errors) == 0, f"Errors under extreme load: {errors[:5]}"
        assert len(successful_selections) == total_expected

        duration = end_time - start_time
        throughput = total_expected / duration
        print(f"Extreme load throughput: {throughput:.2f} selections/second")

        assert throughput > 5000, f"Throughput too low under extreme load: {throughput:.2f}"

        selection_counts = Counter(successful_selections)
        expected_per_server = total_expected // 10
        tolerance = expected_per_server * 0.3  # 30% tolerance for extreme concurrency

        for count in selection_counts.values():
            assert abs(count - expected_per_server) <= tolerance, \
                "Distribution became unfair under extreme load"
