import datetime
from abc import ABCMeta

from bxcommon.messages.bloxroute.key_message import KeyMessage
from bxcommon.utils import logger
from bxcommon.utils.object_hash import ObjectHash
from bxcommon.utils.stats.block_stat_event_type import BlockStatEventType
from bxcommon.utils.stats.block_statistics_service import block_stats


class AbstractBlockchainConnectionProtocol(object):
    __metaclass__ = ABCMeta

    def __init__(self, connection):
        self.connection = connection

    def msg_tx(self, msg):
        """
        Handle a TX message by broadcasting to the entire network
        """
        blx_txmsgs = self.connection.message_converter.tx_to_bx_txs(msg, self.connection.network_num)

        for (blx_txmsg, tx_hash, tx_bytes) in blx_txmsgs:
            # All connections outside of this one is a bloXroute server
            logger.debug("Broadcasting the transaction to peers")
            self.connection.node.broadcast(blx_txmsg, self.connection)
            self.connection.node.get_tx_service().hash_to_contents[tx_hash] = tx_bytes

    def msg_block(self, msg):
        """
        Handle a block message. Sends to node for encryption, then broadcasts.
        """
        block_hash = msg.block_hash()
        block_stats.add_block_event_by_block_hash(block_hash, BlockStatEventType.BLOCK_RECEIVED_FROM_BLOCKCHAIN_NODE)

        if block_hash in self.connection.node.blocks_seen.contents:
            block_stats.add_block_event_by_block_hash(block_hash,
                                                      BlockStatEventType.BLOCK_RECEIVED_FROM_BLOCKCHAIN_NODE_IGNORE_SEEN)
            logger.debug("Have seen block {0} before. Ignoring.".format(block_hash))
            return

        compress_start = datetime.datetime.utcnow()
        bx_block = self.connection.message_converter.block_to_bx_block(msg, self.connection.node.get_tx_service())
        compress_end = datetime.datetime.utcnow()
        block_stats.add_block_event_by_block_hash(block_hash,
                                                  BlockStatEventType.BLOCK_COMPRESSED,
                                                  start_date_time=compress_start,
                                                  end_date_time=compress_end,
                                                  original_size=len(msg.rawbytes()),
                                                  compressed_size=len(bx_block))

        self.connection.node.neutrality_service.propagate_block_to_network(bx_block, self.connection, block_hash)

        self.connection.node.block_recovery_service.cancel_recovery_for_block(block_hash)
        self.connection.node.blocks_seen.add(block_hash)

    def msg_proxy_request(self, msg):
        """
        Handle a chainstate request message.
        """
        self.connection.node.send_msg_to_remote_node(msg)

    def msg_proxy_response(self, msg):
        """
        Handle a chainstate response message.
        """
        self.connection.node.send_msg_to_node(msg)

    def send_key(self, block_hash):
        """
        Sends out the decryption key for a block hash.
        """
        key = self.connection.node.in_progress_blocks.get_encryption_key(block_hash)
        key_message = KeyMessage(ObjectHash(block_hash), key, self.connection.network_num)
        conns = self.connection.node.broadcast(key_message, self.connection)
        block_stats.add_block_event_by_block_hash(block_hash,
                                                  BlockStatEventType.ENC_BLOCK_KEY_SENT_FROM_GATEWAY_TO_PEER,
                                                  peers=map(lambda conn: (conn.peer_desc, conn.CONNECTION_TYPE), conns))