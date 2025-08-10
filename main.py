import uvicorn
import atexit
import signal
import sys
import logging

from load_balancer.api import app, set_load_balancer
from load_balancer.config import load_config
from load_balancer.algorithms.base import Server
from load_balancer.algorithms.round_robin import RoundRobin
from load_balancer.health_checker import HealthChecker

# Global health checker instance
health_checker_instance = None
logger = logging.getLogger(__name__)


def initialize_load_balancer():
    """
    Initializes the load balancer from the configuration.
    """
    config = load_config()
    lb_config = config.get("load_balancer", {})

    algorithm_name = lb_config.get("algorithm", {})
    servers_config = lb_config.get("servers", {})

    match algorithm_name:
        case "round_robin":
            lb = RoundRobin()
        case _:
            raise ValueError(f"Unknown algorithm: {algorithm_name}")

    for server_id, server_info in servers_config.items():
        server = Server(
            id=server_id,
            address=server_info["address"],
            port=server_info["port"],
        )
        lb.add_server(server)

    return lb

def initialize_health_checker(lb_instance):
    """
    Initialize and start the health checker.
    """
    config = load_config()
    health_config = config.get("health_checks", {})

    if not health_config.get("enabled", True):
        logger.info("Health checker is disabled in configuration")
        return None

    interval = health_config.get("interval", 30)  # Default 30 seconds

    global health_checker_instance
    health_checker_instance = HealthChecker(lb_instance, interval)
    health_checker_instance.start()

    logger.info(f"Health checker started with {interval}s interval")
    return health_checker_instance


def shutdown_health_checker():
    """
    Stop the health checker gracefully.
    """
    global health_checker_instance
    if health_checker_instance:
        logger.info("Stopping health checker...")
        health_checker_instance.stop()
        health_checker_instance = None
        logger.info("Health checker stopped")


def signal_handler(signum, frame):
    """
    Handle shutdown signals gracefully.
    """
    logger.info(f"Received signal {signum}, shutting down...")
    shutdown_health_checker()
    sys.exit(0)


@app.on_event("startup")
async def startup_event():
    """Initialize the load balancer and start the health checker."""
    try:
        lb_instance = initialize_load_balancer()
        set_load_balancer(lb_instance)

        # Initialize and start health checker
        initialize_health_checker(lb_instance)

        logger.info("LimeLoad started successfully")
    except Exception as e:
        logger.error(f"Failed to start LimeLoad: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of health checker and other resources."""
    logger.info("LimeLoad is shutting down...")
    shutdown_health_checker()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Register cleanup function for normal exit
    atexit.register(shutdown_health_checker)

    try:
        config = load_config()
        fastapi_config = config.get("fastapi", {})
        host = fastapi_config.get("host", "0.0.0.0")
        port = fastapi_config.get("port")

        logger.info(f"Starting LimeLoad on {host}:{port}")
        uvicorn.run(app, host=host, port=port)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
    finally:
        shutdown_health_checker()
        logger.info("LimeLoad shutdown complete")
