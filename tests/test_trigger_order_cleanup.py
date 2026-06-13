import importlib
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from exchange.okx import CompatibleGridAPI, OKXExchange
from indicators import Signal, Strength


class FakeIndicators:
    def atr(self, df: pd.DataFrame) -> pd.DataFrame:
        updated = df.copy()
        updated["ATR"] = [5.0, 5.0, 5.0]
        return updated

    def supertrend_summary(self, df: pd.DataFrame) -> Signal:
        return Signal(
            trend=1,
            strength=Strength.STRONG,
            supertrend=100.0,
            is_reversal=False,
            before_reversal_supertrend=95.0,
        )


class FakeExchange:
    def __init__(self):
        self.cancel_trigger_orders = MagicMock()
        self.place_limit_order = MagicMock()
        self.update_stop_price = MagicMock()
        self.open_grid_if_not_exist = MagicMock()
        self.close_grid_if_exist = MagicMock()
        self.open_position = MagicMock()

    def get_kline_data(self, symbol: str, bar: str):
        return [{"timestamp": 1}]

    def convert_kline_to_dataframe(self, kline_data):
        return pd.DataFrame(
            {
                "open": [90.0, 100.0, 110.0],
                "high": [95.0, 120.0, 115.0],
                "low": [85.0, 99.0, 105.0],
                "close": [92.0, 101.0, 112.0],
            }
        )

    def get_positions(self, symbol: str):
        return None


class TriggerOrderCleanupTests(unittest.TestCase):
    def test_main_cancels_trigger_orders_when_flat_and_open_not_allowed(self):
        fake_exchange = FakeExchange()
        with patch("exchange.okx.OKXExchange", return_value=fake_exchange):
            strategy_main = importlib.import_module("main")

        try:
            original_exchange = strategy_main.okx_client
            original_indicators = strategy_main.indicators
            strategy_main.okx_client = fake_exchange
            strategy_main.indicators = FakeIndicators()
            strategy_main.main()
        finally:
            strategy_main.okx_client = original_exchange
            strategy_main.indicators = original_indicators

        fake_exchange.cancel_trigger_orders.assert_called_once_with(symbol=strategy_main.symbol)
        fake_exchange.place_limit_order.assert_not_called()

    def test_cancel_trigger_orders_cancels_all_pending_trigger_algos(self):
        exchange = OKXExchange.__new__(OKXExchange)
        exchange.trade = MagicMock()
        exchange.trade.order_algos_list.return_value = {
            "data": [{"algoId": "1"}, {"algoId": "2"}]
        }
        exchange.trade.cancel_algo_order = MagicMock()

        exchange.cancel_trigger_orders("BTC-USDT-SWAP")

        self.assertEqual(exchange.trade.cancel_algo_order.call_count, 2)

    def test_compatible_grid_api_passes_trigger_params_through(self):
        grid = CompatibleGridAPI.__new__(CompatibleGridAPI)
        grid._request_with_params = MagicMock(return_value={"code": "0"})

        result = grid.grid_order_algo(
            instId="BTC-USDT-SWAP",
            algoOrdType="contract_grid",
            maxPx="110000",
            minPx="90000",
            gridNum="20",
            runType="1",
            sz="300",
            direction="long",
            lever="5",
            basePos=True,
            triggerParams={"triggerPx": "100000"},
        )

        self.assertEqual(result, {"code": "0"})
        request_params = grid._request_with_params.call_args.args[2]
        self.assertEqual(request_params["triggerParams"], {"triggerPx": "100000"})


if __name__ == "__main__":
    unittest.main()
