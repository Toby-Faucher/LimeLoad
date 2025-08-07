# Todo Tests

## Config
- [x] Test loading a valid config file
- [x] Test loading a missing config file
- [x] Test loading a config file with invalid JSON
- [x] Test loading a config file with missing keys
- [ ] Test loading an empty config file
- [ ] Test loading a config file with incorrect permissions
- [ ] Test loading a config file that is a directory
- [ ] Test loading a config file with an empty JSON object
- [ ] Test loading a config file with incorrect data types

## Server
- [ ] Test creating a server with a weight
- [ ] Test creating a server with metadata
- [ ] Test server equality
- [ ] Test server hashing

## ServerMetrics
- [ ] Test `is_stale` method

## LoadBalancingAlgorithm
- [ ] Test adding a server that already exists
- [ ] Test removing a server that does not exist
- [ ] Test updating metrics for a server that does not exist
- [ ] Test updating status for a server that does not exist
- [ ] Test getting a server that does not exist
- [ ] Test selecting a server with no healthy servers
- [ ] Test resetting statistics
- [ ] Test `_validate_server` with an invalid server
- [ ] Test `on_server_metrics_updated` hook

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
