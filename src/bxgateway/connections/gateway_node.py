import socket
from collections import deque

from bxcommon.connections.abstract_node import AbstractNode
from bxcommon.utils import logger
from bxgateway.connections.btc_node_connection import BTCNodeConnection
from bxgateway.connections.relay_connection import RelayConnection


class GatewayNode(AbstractNode):
    def __init__(self, server_ip, server_port, servers, node_addr, node_params):
        super(GatewayNode, self).__init__(server_ip, server_port)

        self.servers = servers  # A list of (ip, port) pairs of other bloXroute servers
        self.idx = 0
        self.node_addr = node_addr  # The address of the blockchain node this client is connected to
        self.node_params = node_params
        self.node_conn = None  # Connection object for the blockchain node
        self.node_msg_queue = deque()

    def can_retry_after_destroy(self, teardown, conn):
        # If the connection is to a bloXroute server, then retry it unless we're tearing down the Node
        return not teardown and conn.is_server

    def get_connection_class(self, ip=None):
        return BTCNodeConnection if self.node_addr[0] == ip else RelayConnection

    def connect_to_peers(self):
        for idx in self.servers:
            ip, port = self.servers[idx]
            logger.debug("connecting to relay node {0}:{1}".format(ip, port))
            self.connect_to_address(RelayConnection, socket.gethostbyname(ip), port, setup=True)

        self.connect_to_address(BTCNodeConnection, socket.gethostbyname(self.node_addr[0]), self.node_addr[1],
                                setup=True)

    # Sends a message to the node that this is connected to
    def send_bytes_to_node(self, msg):
        if self.node_conn is not None:
            logger.debug("Sending message to node: " + repr(msg))
            self.node_conn.enqueue_msg_bytes(msg)
        else:
            logger.debug("Adding things to node's message queue")
            self.node_msg_queue.append(msg)