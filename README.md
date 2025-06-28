# LimeLoad
A simple load balancer

## Performance Improvements
- **Pre-parsed URLs**: The `Backend` class now pre-parses the URL and stores the base URL to avoid repeated parsing and string formatting during health checks and request proxying.

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
