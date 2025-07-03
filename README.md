<h2 align="center">
    LimeLoad 🍋‍🟩
    <br>
    LimeLoad: A *nano* load balancer 💚
</h2>

## TODO List

### Core Infrastructure
- [ ] **Configuration File**: Implement a YAML or JSON configuration file for settings, backends, and algorithm selection.
- [ ] **Asynchronous Operations**: Convert the core engine to `asyncio` for non-blocking I/O and improved concurrency.
- [ ] **Logging and Monitoring**: Integrate a structured logging library (e.g., `structlog`) and expose a `/metrics` endpoint for Prometheus scraping.
- [ ] **Dynamic Backend Management**: Implement a REST API or a file-based watcher to add/remove backends at runtime.

### Load Balancing Algorithms
- [ ] **Weighted Round Robin**: Implement a weighted round-robin algorithm where servers with higher weights receive more requests.
- [ ] **Least Connections**: Implement a least-connections algorithm that directs traffic to the server with the fewest active connections.
- [ ] **IP Hash**: Implement an IP hash algorithm for session persistence, ensuring a client is consistently directed to the same server.
- [ ] **Advanced Algorithm Integration**: Design the system to allow for the dynamic selection and chaining of multiple algorithms (e.g., weighted round-robin with a least-connections fallback).

### Health Checks and Monitoring
- [ ] **Customizable Health Checks**: Allow for user-defined health check endpoints, intervals, and protocols (e.g., TCP, ICMP).
- [ ] **Circuit Breaker**: Implement a circuit breaker pattern to automatically eject unhealthy servers from the pool and gracefully re-introduce them when they recover.
- [ ] **Server Metrics**: Enhance the `ServerMetrics` class to track more detailed performance data, such as success/failure rates, latency distribution, and throughput.

### Security and Reliability
- [ ] **HTTPS Support**: Add SSL/TLS termination to secure client-to-load-balancer communication.
- [ ] **Rate Limiting**: Implement a rate-limiting mechanism to protect backend servers from traffic spikes.
- [ ] **Request Timeouts**: Implement configurable timeouts for both client and backend connections to prevent long-running requests from hogging resources.

### Testing and Documentation
- [ ] **Comprehensive Unit Tests**: Write extensive unit tests for all new components, including each load balancing algorithm and the core infrastructure.
- [ ] **Integration Tests**: Develop integration tests to verify the end-to-end functionality of the load balancer.
- [ ] **Documentation**: Update the documentation to reflect the new features, architecture, and configuration options.

## Current Objective List

### Advanced Load Balancing Algorithms
- [x] Research and select specific advanced load balancing algorithms (e.g., Least Connections, Weighted Round Robin, IP Hash).
- [ ] Design a common interface or abstract base class for new load balancing algorithms (e.g., `load_balancer/algorithms/base.py`). *currently working on!*
- [ ] Implement each selected algorithm as a separate class/module within `load_balancer/algorithms/` (e.g., `least_connections.py`, `weighted_round_robin.py`).
- [ ] Modify the main load balancer logic (`main.py` or `pool.py`) to dynamically select and use the chosen algorithm.
- [ ] Consider adding a configuration mechanism (e.g., a new `config.py` file or extending `main.py`'s argument parsing) to allow users to specify the desired algorithm.
- [ ] Write comprehensive unit tests for each new load balancing algorithm to ensure correctness and cover edge cases (e.g., `tests/test_algorithms.py`).
- [ ] Update the `README.md` with documentation on how to configure and use the new load balancing algorithms.

## Future Enhancements
- **Dynamic Backend Management**: Allow adding/removing backends at runtime without restarting the load balancer.
- **Asynchronous Operations**: Utilize `asyncio` for non-blocking I/O to handle more concurrent connections efficiently.
- **Configuration File**: Externalize backend configurations into a file (e.g., YAML, JSON) for easier management.
- **Logging and Monitoring**: Add comprehensive logging for requests, errors, and backend health, and integrate with monitoring tools.
- **HTTPS Support**: Implement SSL/TLS termination for secure communication.
- **Circuit Breaker Pattern**: Implement a circuit breaker to prevent requests from being sent to unhealthy backends, allowing them time to recover.
- **Rate Limiting**: Add the ability to limit the number of requests per client or per backend.
- **Caching**: Implement a caching mechanism to serve frequently requested content directly from the load balancer.
- **Health Check Improvements**: More robust health checks, including custom health check endpoints and different protocols (e.g., TCP, ICMP).
