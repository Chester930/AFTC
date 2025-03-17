# 測試情境：假裝日圓突然大跌
# 預期結果：交易機器人應該要自動買入 ✅
# 就像消防演習，假裝失火測試應變能力 🔥→🚒

import unittest
import logging
import json
from datetime import datetime, timedelta

# 導入要測試的組件
from core.engine.trading_bot import TradingBot
from core.database.realtime_data import RealtimeDataManager
from strategies.single_currency.simple_strategy import SimpleStrategy


class MockDataManager:
    """
    模擬數據管理器 - 用於測試，返回預定義的數據
    """
    def __init__(self, mock_data_sequence):
        self.mock_data_sequence = mock_data_sequence
        self.current_index = 0
    
    def get_latest_data(self):
        """返回當前模擬數據"""
        if self.current_index < len(self.mock_data_sequence):
            data = self.mock_data_sequence[self.current_index]
            self.current_index += 1
            return data
        return self.mock_data_sequence[-1]  # 如果已經到最後，返回最後一個數據
    
    def close(self):
        """模擬關閉連接"""
        pass


class SingleTradeTest(unittest.TestCase):
    """測試單一貨幣交易策略"""
    
    def setUp(self):
        """測試前準備"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('test')
    
    def test_price_drop_buy_signal(self):
        """測試價格下跌時的買入信號"""
        # 創建測試數據序列 - 模擬USD/JPY價格下跌
        now = datetime.now()
        test_data = [
            # 第一天數據
            {
                "USD/JPY": {
                    "rate": 150.0,
                    "timestamp": now.isoformat()
                }
            },
            # 第二天數據 - 價格下跌 3%
            {
                "USD/JPY": {
                    "rate": 145.5,  # 下跌3%
                    "timestamp": (now + timedelta(days=1)).isoformat()
                }
            }
        ]
        
        # 創建模擬數據管理器
        mock_data_manager = MockDataManager(test_data)
        
        # 創建策略 - 設定閾值為2%，這樣3%的跌幅應該觸發買入
        strategy = SimpleStrategy(currency_pair="USD/JPY", threshold_percent=2.0)
        
        # 創建交易機器人
        bot = TradingBot(mock_data_manager, strategy)
        
        # 模擬第一天 - 不應該交易（首次檢查只是記錄數據）
        result1 = bot.check_and_execute()
        self.assertTrue(result1, "第一次檢查應該成功但不交易")
        self.assertEqual(len(bot.trade_history), 0, "第一次檢查不應該產生交易")
        
        # 模擬第二天 - 應該觸發買入
        result2 = bot.check_and_execute()
        self.assertTrue(result2, "第二次檢查應該成功並交易")
        self.assertEqual(len(bot.trade_history), 1, "應該有一筆交易記錄")
        
        # 檢查交易詳情
        trade = bot.trade_history[0]
        self.assertEqual(trade['action'], 'buy', "應該是買入操作")
        self.assertEqual(trade['currency'], 'USD/JPY', "應該交易USD/JPY")
        self.assertAlmostEqual(trade['price'], 145.5, delta=0.01, msg="價格應該是145.5")
        
        # 關閉機器人
        bot.shutdown()
    
    def test_price_rise_sell_signal(self):
        """測試價格上漲時的賣出信號"""
        # 創建測試數據序列 - 模擬EUR/USD價格上漲
        now = datetime.now()
        test_data = [
            # 第一天數據
            {
                "EUR/USD": {
                    "rate": 1.1000,
                    "timestamp": now.isoformat()
                }
            },
            # 第二天數據 - 價格上漲 2.5%
            {
                "EUR/USD": {
                    "rate": 1.1275,  # 上漲2.5%
                    "timestamp": (now + timedelta(days=1)).isoformat()
                }
            }
        ]
        
        # 創建模擬數據管理器
        mock_data_manager = MockDataManager(test_data)
        
        # 創建策略 - 設定閾值為2%，這樣2.5%的漲幅應該觸發賣出
        strategy = SimpleStrategy(currency_pair="EUR/USD", threshold_percent=2.0)
        
        # 創建交易機器人
        bot = TradingBot(mock_data_manager, strategy)
        
        # 模擬第一天 - 不應該交易（首次檢查只是記錄數據）
        bot.check_and_execute()
        
        # 模擬第二天 - 應該觸發賣出
        bot.check_and_execute()
        
        # 檢查交易詳情
        self.assertEqual(len(bot.trade_history), 1, "應該有一筆交易記錄")
        trade = bot.trade_history[0]
        self.assertEqual(trade['action'], 'sell', "應該是賣出操作")
        self.assertEqual(trade['currency'], 'EUR/USD', "應該交易EUR/USD")
        
        # 關閉機器人
        bot.shutdown()
    
    def test_small_price_change_no_trade(self):
        """測試小幅價格變化時不應交易"""
        # 創建測試數據序列 - 模擬GBP/USD價格小幅變化
        now = datetime.now()
        test_data = [
            # 第一天數據
            {
                "GBP/USD": {
                    "rate": 1.2500,
                    "timestamp": now.isoformat()
                }
            },
            # 第二天數據 - 價格上漲 0.5%
            {
                "GBP/USD": {
                    "rate": 1.2563,  # 上漲0.5%
                    "timestamp": (now + timedelta(days=1)).isoformat()
                }
            }
        ]
        
        # 創建模擬數據管理器
        mock_data_manager = MockDataManager(test_data)
        
        # 創建策略 - 設定閾值為1%，這樣0.5%的變化不應該觸發交易
        strategy = SimpleStrategy(currency_pair="GBP/USD", threshold_percent=1.0)
        
        # 創建交易機器人
        bot = TradingBot(mock_data_manager, strategy)
        
        # 模擬第一天和第二天
        bot.check_and_execute()
        bot.check_and_execute()
        
        # 檢查應該沒有交易
        self.assertEqual(len(bot.trade_history), 0, "不應該有交易記錄")
        
        # 關閉機器人
        bot.shutdown()


if __name__ == "__main__":
    unittest.main() 