from load_balancer.algorithms.base import LoadBalancingAlgorithm, Server, LoadBalancingContext, ServerStatus
from typing import Optional, List

class TestAlgorithm(LoadBalancingAlgorithm):
    def __init__(self):
        super().__init__(name="TestAlgorithm")

    def select_server(self, context: Optional[LoadBalancingContext] = None) -> Optional[Server]:
        with self._lock:
            healthy_servers = self.get_healthy_servers()
            if not healthy_servers:
                self.on_selected_failed(context)
                return None
            
            # Simple logic: just return the first healthy server
            server = healthy_servers[0]
            self.on_server_selected(server, context)
            return server

    def add_server(self, server: Server) -> None:
        with self._lock:
            super().add_server(server)

    def remove_server(self, server_id: str) -> bool:
        with self._lock:
            return super().remove_server(server_id)

if __name__ == "__main__":
    print("Testing Load Balancer Setup")

    # 1. Create a load balancing algorithm instance
    lb = TestAlgorithm()
    print(f"Initialized Algorithm: {lb}")

    # 2. Create server instances
    server1 = Server(id="server1", address="192.168.1.10", port=8080)
    server2 = Server(id="server2", address="192.168.1.11", port=8080, status=ServerStatus.UNHEALTHY)
    server3 = Server(id="server3", address="192.168.1.12", port=8080)

    print(f"\nCreated servers:\n- {server1}\n- {server2}\n- {server3}")

    # 3. Add servers to the load balancer
    lb.add_server(server1)
    lb.add_server(server2)
    lb.add_server(server3)

    print(f"\nServers added to the pool. Total servers: {lb.get_server_count()}")
    print(f"Healthy servers: {lb.get_healthy_server_count()}")
    print(f"Healthy server list: {[s.id for s in lb.get_healthy_servers()]}")


    # 4. Select a server
    print("\nSelecting a server...")
    selected_server = lb.select_server()
    if selected_server:
        print(f"Selected server: {selected_server.id} ({selected_server.endpoint})")
    else:
        print("No server was selected.")
        
    # 5. Test server removal
    print(f"\nRemoving server: {server1.id}")
    lb.remove_server(server1.id)
    print(f"Healthy servers after removal: {lb.get_healthy_server_count()}")

    print("\nSelecting a server again...")
    selected_server = lb.select_server()
    if selected_server:
        print(f"Selected server: {selected_server.id} ({selected_server.endpoint})")
    else:
        print("No server was selected.")

    print("\nTesting statistics:")
    print(lb.get_statistics())
