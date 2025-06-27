# LimeLoad
===
A simple load balancer

## Performance Improvements
- **Pre-parsed URLs**: The `Backend` class now pre-parses the URL and stores the base URL to avoid repeated parsing and string formatting during health checks and request proxying.

## Future Enhancements
- **Advanced Load Balancing Algorithms**: Implement more sophisticated algorithms like Least Connections, Weighted Round Robin, or IP Hash.
- **Dynamic Backend Management**: Allow adding/removing backends at runtime without restarting the load balancer.
- **Asynchronous Operations**: Utilize `asyncio` for non-blocking I/O to handle more concurrent connections efficiently.
- **Configuration File**: Externalize backend configurations into a file (e.g., YAML, JSON) for easier management.
- **Logging and Monitoring**: Add comprehensive logging for requests, errors, and backend health, and integrate with monitoring tools.
- **HTTPS Support**: Implement SSL/TLS termination for secure communication.
- **Circuit Breaker Pattern**: Implement a circuit breaker to prevent requests from being sent to unhealthy backends, allowing them time to recover.
- **Rate Limiting**: Add the ability to limit the number of requests per client or per backend.
- **Caching**: Implement a caching mechanism to serve frequently requested content directly from the load balancer.
- **Health Check Improvements**: More robust health checks, including custom health check endpoints and different protocols (e.g., TCP, ICMP).