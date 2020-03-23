import time
from typing import Optional, Type

from bxcommon.utils.stats.statistics_service import StatisticsService, StatsIntervalData
from bxgateway import gateway_constants
from bxutils.logging.log_record_type import LogRecordType
from bxutils import logging


class GatewayBdnPerformanceStatInterval(StatsIntervalData):
    new_blocks_received_from_blockchain_node: int
    new_blocks_received_from_bdn: int
    new_tx_received_from_blockchain_node: int
    new_tx_received_from_bdn: int

    def __init__(self, *args, **kwargs):
        super(GatewayBdnPerformanceStatInterval, self).__init__(*args, **kwargs)
        self.new_blocks_received_from_blockchain_node = 0
        self.new_blocks_received_from_bdn = 0
        self.new_tx_received_from_blockchain_node = 0
        self.new_tx_received_from_bdn = 0


class _GatewayBdnPerformanceStatsService(StatisticsService):
    INTERVAL_DATA_CLASS = GatewayBdnPerformanceStatInterval

    def __init__(self, interval=gateway_constants.GATEWAY_BDN_PERFORMANCE_STATS_INTERVAL_S,
                 look_back=gateway_constants.GATEWAY_BDN_PERFORMANCE_STATS_LOOKBACK):
        super().__init__(
            "GatewayBdnPerformanceStats",
            interval,
            look_back,
            reset=True,
            logger=logging.get_logger(LogRecordType.BdnPerformanceStats, __name__)
        )

    def get_interval_data_class(self) -> Type[GatewayBdnPerformanceStatInterval]:
        return GatewayBdnPerformanceStatInterval

    def close_interval_data(self):
        self.interval_data.end_time = time.time()
        self.history.append(self.interval_data)

    def log_block_from_blockchain_node(self):
        self.interval_data.new_blocks_received_from_blockchain_node += 1

    def log_block_from_bdn(self):
        self.interval_data.new_blocks_received_from_bdn += 1

    def log_tx_from_blockchain_node(self):
        self.interval_data.new_tx_received_from_blockchain_node += 1

    def log_tx_from_bdn(self):
        self.interval_data.new_tx_received_from_bdn += 1

    def get_info(self):
        pass

    def get_most_recent_stats(self) -> Optional[GatewayBdnPerformanceStatInterval]:
        if self.history:
            interval_data = self.history[0]
            return interval_data
        else:
            return None


gateway_bdn_performance_stats_service = _GatewayBdnPerformanceStatsService()