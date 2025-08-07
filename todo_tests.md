# Todo Tests

## Config
- [x] Test loading a valid config file
- [x] Test loading a missing config file
- [x] Test loading a config file with invalid JSON
- [x] Test loading a config file with missing keys
- [x] Test loading an empty config file
- [x] Test loading a config file with incorrect permissions
- [x] Test loading a config file that is a directory
- [x] Test loading a config file with incorrect data types

## Server
- [x] Test creating a server with a weight
- [x] Test creating a server with metadata
- [x] Test server equality
- [x] Test server hashing

## ServerMetrics
- [x] Test `is_stale` method

## LoadBalancingAlgorithm
- [x] Test adding a server that already exists
- [x] Test removing a server that does not exist
- [x] Test updating metrics for a server that does not exist
- [x] Test updating status for a server that does not exist
- [x] Test getting a server that does not exist
- [x] Test selecting a server with no healthy servers
- [x] Test resetting statistics
- [x] Test `_validate_server` with an invalid server
- [x] Test `on_server_metrics_updated` hook
- [x] Test basic algorithm initialization
- [x] Test adding servers normally
- [x] Test removing servers normally
- [x] Test server selection with healthy servers
- [x] Test server selection with context
- [x] Test algorithm statistics tracking
- [x] Test multiple server handling
- [x] Test server status updates

## Health Checker
- [ ] Test a successful health check
- [ ] Test a failed health check
- [ ] Test a health check with an invalid server IP
- [ ] Test a health check with an invalid server port

## FastAPI
- [ ] Test the `/health/{server_id}` endpoint
- [ ] Test the `/select-server` endpoint

## Main
- [ ] Test that the load balancer is initialized correctly
- [ ] Test that the servers are added to the load balancer
- [ ] Test that the FastAPI app is started
