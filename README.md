<h2 align="center">
    LimeLoad 🍋‍🟩
    <br>
    LimeLoad: A *nano* load balancer 💚
</h2>

## `base.py` Improvement TODO List

This list focuses exclusively on enhancing the `load_balancer/algorithms/base.py` file, improving the core ABC, data structures, and overall robustness of the foundation for all load balancing algorithms.

### 1. Performance Optimizations

-   [x] **Server Storage Mechanism**:
    -   **Problem**: Currently, servers are stored in a `List[Server[ServerType]]`. Operations like `get_server`, `remove_server`, and `update_server_metrics` require iterating through the list, resulting in O(n) time complexity. This is inefficient for a large number of servers.
    -   **Solution**: Refactor `self.servers` to be a `Dict[str, Server[ServerType]]`, where the key is the `server.id`. This will reduce the lookup, removal, and update times to O(1) on average, significantly improving performance as the server pool scales. This change will require updating all methods that interact with the `self.servers` list.

-   [x] **Efficient Healthy Server Retrieval**:
    -   **Problem**: The `get_healthy_servers` method iterates through all servers every time it's called. If called frequently, this can be a performance bottleneck.
    -   **Solution**: Maintain a separate `Set[str]` or `Dict[str, Server[ServerType]]` containing only the healthy servers. This set would be updated whenever a server's status changes (via the `on_server_status_updated` hook). This provides an O(1) lookup for the healthy server collection, though it adds a small overhead to status updates.

### 2. Concurrency and Thread Safety

-   [ ] **Implement Locking for Shared State**:
    -   **Problem**: The `LoadBalancingAlgorithm` class is not thread-safe. If multiple threads access the server list (e.g., one thread adding a server while another is selecting one), it can lead to race conditions and inconsistent state.
    -   **Solution**: Introduce a `threading.Lock` or `asyncio.Lock` to protect critical sections that modify shared state, such as `self.servers` and `self.statistics`. Methods like `add_server`, `remove_server`, and `select_server` should acquire the lock before accessing these shared resources.

### 3. ABC and API Design Enhancements

-   [ ] **Refine Abstract Method Contracts**:
    -   **Problem**: The current abstract methods (`select_server`, `add_server`, `remove_server`) are minimal. Their contracts are not explicit enough, which can lead to inconsistent behavior in subclasses.
    -   **Solution**: Flesh out the docstrings and type hinting for each abstract method to create a clear and prescriptive contract for implementers. This includes defining expected behavior, return values, and error conditions for various scenarios.
        -   **`select_server(context: LoadBalancingContext) -> Server`**:
            -   **Success Condition**: Must return a healthy `Server` instance from the pool.
            -   **Failure Condition**: What should happen if no healthy servers are available? The contract should specify whether to:
                -   Raise a specific exception (e.g., `NoHealthyServersError`).
                -   Return `None` and let the caller handle it.
                -   Block until a server becomes available (not recommended for the base contract).
            -   **Context Usage**: Clarify how the `LoadBalancingContext` should be used. Should the implementation prioritize servers with lower latency, fewer connections, or other metrics contained within the context?
        -   **`add_server(server: Server)`**:
            -   **Duplicate Servers**: Define the behavior when a server with a duplicate `server.id` is added. Should it:
                -   Raise a `ValueError` or a custom `DuplicateServerError`?
                -   Update the existing server's information?
                -   Silently ignore the operation? (The contract should explicitly forbid this).
            -   **Validation**: The contract should state that the server must be validated before being added to the pool. The base class should handle this validation to ensure consistency.
        -   **`remove_server(server_id: str)`**:
            -   **Server Not Found**: Specify the behavior if `server_id` does not exist in the server pool. Should it raise a `KeyError` or a custom `ServerNotFoundError`?
            -   **Return Value**: Define what the method should return on successful removal. Should it be the removed `Server` object or `None`?
        -   **Helper Methods**:
            -   Consider if any helper methods, such as `_validate_server` or a potential `_update_server_health`, should be made abstract or have their contracts more clearly defined to ensure subclasses implement them correctly.

-   [ ] **State Management Hooks**:
    -   **Problem**: The hooks (`on_server_added`, etc.) are useful but could be more powerful.
    -   **Solution**: Consider implementing a more formal event dispatcher or observer pattern. This would allow multiple components to listen for events (like `server_added`) without modifying the base class, promoting better separation of concerns.

### 4. Configuration and Flexibility

-   [ ] **Decouple Hardcoded Values**:
    -   **Problem**: The `ServerMetrics.is_stale` method has a hardcoded `threshold` of 30 seconds.
    -   **Solution**: Abstract this value out. Pass a configuration object or dictionary during the `LoadBalancingAlgorithm` initialization. This configuration could hold values like the staleness threshold, logging levels, and other tunable parameters, making the base class more flexible.

### 5. Data Structure and Validation Improvements

-   [ ] **Immutable Data Classes**:
    -   **Problem**: The dataclasses (`Server`, `ServerMetrics`, `LoadBalancingContext`) are mutable. In a concurrent environment or complex system, this can lead to unexpected side effects where data is changed unintentionally.
    -   **Solution**: Evaluate making some of these dataclasses immutable by setting `frozen=True`. This is particularly relevant for `LoadBalancingContext`, which represents a snapshot in time. This change would force more explicit state updates and can help prevent bugs.

-   [ ] **Enhanced Server Validation**:
    -   **Problem**: The `_validate_server` method is basic. It doesn't prevent invalid servers from being added if a subclass forgets to call it.
    -   **Solution**: Integrate the validation logic directly into `add_server` within the base class, making it non-abstract. Subclasses can still override it but will have a safe default. Raise a specific `ValueError` or a custom exception (e.g., `InvalidServerConfiguration`) if validation fails to provide clearer error feedback.

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
