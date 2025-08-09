#!/usr/bin/env python3
"""
Demo script showing the Round Robin load balancing algorithm in action.

This script demonstrates:
- Basic round robin selection
- Server health status changes
- Concurrent load balancing
- Statistics tracking
"""

import time
import threading
from collections import Counter

from load_balancer.algorithms.round_robin import RoundRobin
from load_balancer.algorithms.base import Server, ServerStatus, LoadBalancingContext


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*50}")
    print(f" {title}")
    print('='*50)


def demo_basic_round_robin():
    """Demonstrate basic round robin behavior."""
    print_section("Basic Round Robin Selection")

    # Create round robin instance
    rr = RoundRobin()

    # Add servers
    servers = [
        Server(id="web1", address="192.168.1.10", port=8080),
        Server(id="web2", address="192.168.1.11", port=8080),
        Server(id="web3", address="192.168.1.12", port=8080),
    ]

    for server in servers:
        rr.add_server(server)
        print(f"Added server: {server.id} ({server.endpoint})")

    print(f"\nServers in pool: {rr.get_server_count()}")
    print(f"Healthy servers: {rr.get_healthy_server_count()}")

    # Demonstrate round robin selection
    print("\nRound Robin Selection Pattern:")
    selections = []
    for i in range(12):  # 4 complete cycles
        selected = rr.select_server()
        selections.append(selected.id)
        print(f"Request {i+1:2d}: → {selected.id} ({selected.endpoint})")

    # Show distribution
    counts = Counter(selections)
    print(f"\nDistribution: {dict(counts)}")


def demo_server_health_management():
    """Demonstrate server health status management."""
    print_section("Server Health Management")

    rr = RoundRobin()

    # Add servers
    servers = [
        Server(id="app1", address="10.0.1.10", port=8080),
        Server(id="app2", address="10.0.1.11", port=8080),
        Server(id="app3", address="10.0.1.12", port=8080),
    ]

    for server in servers:
        rr.add_server(server)

    print("Initial selections (all servers healthy):")
    for i in range(6):
        selected = rr.select_server()
        print(f"  Request {i+1}: → {selected.id}")

    # Mark one server as unhealthy
    print(f"\n🔴 Marking app2 as UNHEALTHY...")
    rr.update_server_status("app2", ServerStatus.UNHEALTHY)
    print(f"Healthy servers: {rr.get_healthy_server_count()}/3")

    print("\nSelections with app2 unhealthy:")
    selections = []
    for i in range(8):
        selected = rr.select_server()
        selections.append(selected.id)
        print(f"  Request {i+1}: → {selected.id}")

    print(f"Distribution: {dict(Counter(selections))}")
    print("Note: app2 is not selected while unhealthy")

    # Recover the server
    print(f"\n🟢 Recovering app2 to HEALTHY...")
    rr.update_server_status("app2", ServerStatus.HEALTHY)
    print(f"Healthy servers: {rr.get_healthy_server_count()}/3")

    print("\nSelections after recovery:")
    for i in range(6):
        selected = rr.select_server()
        print(f"  Request {i+1}: → {selected.id}")


def demo_concurrent_load_balancing():
    """Demonstrate thread-safe concurrent load balancing."""
    print_section("Concurrent Load Balancing")

    rr = RoundRobin()

    # Add servers
    for i in range(4):
        server = Server(id=f"api{i+1}", address=f"172.16.0.{i+10}", port=8080)
        rr.add_server(server)

    print(f"Created load balancer with {rr.get_server_count()} servers")

    # Shared results
    results = []
    results_lock = threading.Lock()

    def worker(worker_id, num_requests):
        """Worker function that makes load balancing requests."""
        worker_results = []

        for i in range(num_requests):
            selected = rr.select_server()
            timestamp = time.time()
            worker_results.append({
                'worker': worker_id,
                'request': i + 1,
                'server': selected.id,
                'timestamp': timestamp
            })
            # Small delay to simulate request processing
            time.sleep(0.001)

        with results_lock:
            results.extend(worker_results)

    # Start multiple worker threads
    num_workers = 4
    requests_per_worker = 10
    threads = []

    print(f"\nStarting {num_workers} workers, each making {requests_per_worker} requests...")
    start_time = time.time()

    for worker_id in range(num_workers):
        thread = threading.Thread(
            target=worker,
            args=(worker_id + 1, requests_per_worker)
        )
        threads.append(thread)
        thread.start()

    # Wait for all workers to complete
    for thread in threads:
        thread.join()

    end_time = time.time()
    duration = end_time - start_time

    # Analyze results
    print(f"\nCompleted {len(results)} requests in {duration:.3f} seconds")
    print(f"Throughput: {len(results)/duration:.1f} requests/second")

    # Show distribution
    server_counts = Counter(r['server'] for r in results)
    print(f"\nServer distribution: {dict(server_counts)}")

    # Show worker breakdown
    print("\nPer-worker results:")
    for worker_id in range(1, num_workers + 1):
        worker_requests = [r for r in results if r['worker'] == worker_id]
        worker_servers = [r['server'] for r in worker_requests]
        print(f"  Worker {worker_id}: {' → '.join(worker_servers)}")


def demo_load_balancing_context():
    """Demonstrate load balancing with request context."""
    print_section("Load Balancing with Context")

    rr = RoundRobin()

    # Add servers
    for i in range(3):
        server = Server(id=f"svc{i+1}", address=f"10.1.0.{i+10}", port=9000)
        rr.add_server(server)

    # Different request contexts
    contexts = [
        LoadBalancingContext(
            client_ip="203.0.113.100",
            request_path="/api/users",
            request_method="GET"
        ),
        LoadBalancingContext(
            client_ip="203.0.113.101",
            request_path="/api/orders",
            request_method="POST"
        ),
        LoadBalancingContext(
            client_ip="203.0.113.102",
            request_path="/api/products",
            request_method="GET"
        ),
    ]

    print("Round robin selection with different contexts:")
    print("(Note: Round robin ignores context - selection is purely sequential)")
    print()

    for i, context in enumerate(contexts * 3):  # Repeat contexts 3 times
        selected = rr.select_server(context)
        print(f"Request {i+1:2d}: {context.client_ip} {context.request_method:4s} "
              f"{context.request_path:15s} → {selected.id}")


def demo_statistics_tracking():
    """Demonstrate statistics tracking."""
    print_section("Statistics Tracking")

    rr = RoundRobin()

    # Add servers
    for i in range(3):
        server = Server(id=f"node{i+1}", address=f"10.2.0.{i+10}", port=8080)
        rr.add_server(server)

    print("Initial statistics:")
    stats = rr.get_statistics()
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Successful selections: {stats['successful_selections']}")
    print(f"  Failed selections: {stats['failed_selections']}")
    print(f"  Success rate: {stats['success_rate']:.2%}")

    # Make some successful requests
    print(f"\nMaking 15 successful requests...")
    for i in range(15):
        selected = rr.select_server()
        if i < 5:
            print(f"  Request {i+1}: → {selected.id}")
        elif i == 5:
            print("  ... (continuing)")

    # Simulate a failure scenario
    print(f"\nSimulating failure scenario (no healthy servers)...")
    # Mark all servers as unhealthy
    for i in range(3):
        rr.update_server_status(f"node{i+1}", ServerStatus.UNHEALTHY)

    # Try to make a request (will fail)
    try:
        rr.select_server()
    except Exception as e:
        print(f"  Expected failure: {e}")

    # Restore one server
    rr.update_server_status("node1", ServerStatus.HEALTHY)

    # Make more successful requests
    print(f"\nMaking 5 more requests after recovery...")
    for i in range(5):
        selected = rr.select_server()
        print(f"  Request {i+1}: → {selected.id}")

    # Final statistics
    print(f"\nFinal statistics:")
    stats = rr.get_statistics()
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Successful selections: {stats['successful_selections']}")
    print(f"  Failed selections: {stats['failed_selections']}")
    print(f"  Success rate: {stats['success_rate']:.2%}")
    print(f"  Algorithm: {stats['algorithm_name']}")
    print(f"  Server count: {stats['server_count']}")
    print(f"  Healthy servers: {stats['healthy_server_count']}")


def main():
    """Run all demonstrations."""
    print("Round Robin Load Balancer Demo")
    print("This demo showcases the Round Robin load balancing algorithm")

    try:
        demo_basic_round_robin()
        time.sleep(1)

        demo_server_health_management()
        time.sleep(1)

        demo_concurrent_load_balancing()
        time.sleep(1)

        demo_load_balancing_context()
        time.sleep(1)

        demo_statistics_tracking()

        print_section("Demo Complete")
        print("The Round Robin algorithm provides:")
        print("✓ Fair distribution of requests across servers")
        print("✓ Simple and predictable selection pattern")
        print("✓ Automatic handling of unhealthy servers")
        print("✓ Thread-safe concurrent operation")
        print("✓ Comprehensive statistics tracking")

    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
