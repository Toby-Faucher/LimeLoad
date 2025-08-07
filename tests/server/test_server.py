from re import S
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from load_balancer.algorithms.base import Server, ServerStatus

def create_server(id="test", address="localhost", port=8080):
    return Server(id=id, address=address, port=port)

def test_server_creation():
    server = create_server()
    assert server.id == "test"
    assert server.address == "localhost"
    assert server.port == 8080

def test_server_weight():
    server = create_server()
    #TODO: make server weight
    assert server.weight == 1

def test_server_status():
    server = create_server()
    server.status = ServerStatus.MAINTENANCE
    assert server.status == ServerStatus.MAINTENANCE

def test_server_metadata():
    server = create_server()
    server.metadata = {
        "region": "us-east-1",
        "data_center": "us-east-1a",
        "instance_type": "t2.micro"
    }
    assert server.metadata == {
        "region": "us-east-1",
        "data_center": "us-east-1a",
        "instance_type": "t2.micro"
    }
