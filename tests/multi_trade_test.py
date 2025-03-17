# 測試情境：假裝歐元和英鎊的價格走勢突然不同步
# 預期結果：交易機器人應該要抓住這個機會交易 ✅
# 就像在圖書館看到兩本相關的書突然被分開，找出機會

import unittest
import logging
import json
from datetime import datetime, timedelta

# 導入要測試的組件
from core.engine.trading_bot import TradingBot
from strategies.multi_currency.correlation_strategy import CorrelationStrategy


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


class MockHistoricalDataManager:
    """
    模擬歷史數據管理器 - 用於測試，替換相關性策略中的歷史數據訪問
    """
    def __init__(self, correlation=0.8):
        self.correlation = correlation
    
    def load_historical_data(self, currency_pair, start_date=None, end_date=None):
        """返回假的歷史數據"""
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        
        # 創建30天的假數據
        dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
        
        # 反轉順序，使日期從早到晚
        dates.reverse()
        
        # 假設所有匯率都從1開始，然後隨機波動
        np.random.seed(hash(currency_pair) % 100)  # 不同貨幣對有不同的隨機種子
        rates = np.cumsum(np.random.normal(0, 0.01, len(dates))) + 1.0
        
        # 創建DataFrame
        df = pd.DataFrame({
            'date': pd.to_datetime(dates),
            'rate': rates
        }).set_index('date')
        
        return df
    
    def get_correlation(self, pair1, pair2, window=30, start_date=None, end_date=None):
        """返回假的相關性數據"""
        import pandas as pd
        import numpy as np
        
        # 創建一個固定的相關性序列
        corr_values = np.ones(window) * self.correlation
        index = pd.date_range(end=datetime.now(), periods=window)
        
        return pd.Series(corr_values, index=index)


# 預設相關性策略的歷史數據管理器為我們的模擬版本
CorrelationStrategy.historical_data = MockHistoricalDataManager()


class MultiTradeTest(unittest.TestCase):
    """測試多貨幣交易策略"""
    
    def setUp(self):
        """測試前準備"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('test')
    
    def test_correlation_divergence_signal(self):
        """測試相關性分歧時的交易信號"""
        # 創建測試數據序列 - 模擬EUR/USD和GBP/USD價格分歧
        now = datetime.now()
        
        # 第一天數據 - 基準
        day1_data = {
            "EUR/USD": {
                "rate": 1.1000,
                "timestamp": now.isoformat()
            },
            "GBP/USD": {
                "rate": 1.2500,
                "timestamp": now.isoformat()
            },
            "AUD/USD": {
                "rate": 0.7000,
                "timestamp": now.isoformat()
            }
        }
        
        # 第二天數據 - EUR/USD上漲2%，但GBP/USD下跌1%，造成分歧
        day2_data = {
            "EUR/USD": {
                "rate": 1.1220,  # 上漲2%
                "timestamp": (now + timedelta(days=1)).isoformat()
            },
            "GBP/USD": {
                "rate": 1.2375,  # 下跌1%
                "timestamp": (now + timedelta(days=1)).isoformat()
            },
            "AUD/USD": {
                "rate": 0.7070,  # 上漲1%
                "timestamp": (now + timedelta(days=1)).isoformat()
            }
        }
        
        # 模擬數據序列
        test_data = [day1_data, day2_data]
        
        # 創建模擬數據管理器
        mock_data_manager = MockDataManager(test_data)
        
        # 創建策略 - 設定閾值為0.01（1%），這樣分歧足以觸發交易
        strategy = CorrelationStrategy(
            primary_pair="EUR/USD",
            secondary_pairs=["GBP/USD", "AUD/USD"],
            correlation_window=30,
            divergence_threshold=0.01
        )
        
        # 替換策略中的歷史數據管理器
        strategy.historical_data = MockHistoricalDataManager(correlation=0.9)
        
        # 創建交易機器人
        bot = TradingBot(mock_data_manager, strategy)
        
        # 模擬第一天 - 不應該交易（首次檢查只是記錄數據）
        bot.check_and_execute()
        
        # 模擬第二天 - 應該觸發交易
        bot.check_and_execute()
        
        # 檢查交易詳情
        self.assertGreater(len(bot.trade_history), 0, "應該有交易記錄")
        if len(bot.trade_history) > 0:
            trade = bot.trade_history[0]
            self.assertEqual(trade['currency'], 'EUR/USD', "應該交易EUR/USD")
            self.logger.info(f"交易詳情: {trade}")
        
        # 關閉機器人
        bot.shutdown()
    
    def test_no_divergence_no_trade(self):
        """測試當沒有分歧時不應交易"""
        # 創建測試數據序列 - 模擬EUR/USD和GBP/USD同時上漲
        now = datetime.now()
        
        # 第一天數據 - 基準
        day1_data = {
            "EUR/USD": {
                "rate": 1.1000,
                "timestamp": now.isoformat()
            },
            "GBP/USD": {
                "rate": 1.2500,
                "timestamp": now.isoformat()
            }
        }
        
        # 第二天數據 - 兩個貨幣對都上漲1%
        day2_data = {
            "EUR/USD": {
                "rate": 1.1110,  # 上漲1%
                "timestamp": (now + timedelta(days=1)).isoformat()
            },
            "GBP/USD": {
                "rate": 1.2625,  # 上漲1%
                "timestamp": (now + timedelta(days=1)).isoformat()
            }
        }
        
        # 模擬數據序列
        test_data = [day1_data, day2_data]
        
        # 創建模擬數據管理器
        mock_data_manager = MockDataManager(test_data)
        
        # 創建策略 - 設定閾值為0.02（2%）
        strategy = CorrelationStrategy(
            primary_pair="EUR/USD",
            secondary_pairs=["GBP/USD"],
            correlation_window=30,
            divergence_threshold=0.02
        )
        
        # 替換策略中的歷史數據管理器
        strategy.historical_data = MockHistoricalDataManager(correlation=0.9)
        
        # 創建交易機器人
        bot = TradingBot(mock_data_manager, strategy)
        
        # 模擬兩天
        bot.check_and_execute()
        bot.check_and_execute()
        
        # 檢查不應該有交易
        self.assertEqual(len(bot.trade_history), 0, "不應該有交易記錄")
        
        # 關閉機器人
        bot.shutdown()


if __name__ == "__main__":
    unittest.main() 