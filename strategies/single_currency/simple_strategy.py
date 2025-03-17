# 策略說明：當日圓比昨天便宜5%時買入
# 就像看到漫畫特價就馬上購買 📉→🛒
# 計算方式：比較今日與昨日價格

import logging
from datetime import datetime, timedelta


class SimpleStrategy:
    """
    簡單交易策略 - 當某個貨幣對價格變化超過閾值時買入或賣出
    就像發現漫畫特價時馬上購買，或發現價格上漲時出售
    """
    
    def __init__(self, currency_pair="USD/JPY", threshold_percent=0.5, trade_amount=1000):
        """
        初始化簡單策略
        
        Args:
            currency_pair: 交易的貨幣對
            threshold_percent: 價格變化閾值（百分比）
            trade_amount: 交易金額
        """
        self.currency_pair = currency_pair
        self.threshold_percent = threshold_percent
        self.trade_amount = trade_amount
        self.previous_rate = None
        self.logger = logging.getLogger('simple_strategy')
        self.logger.info(f"簡單策略已初始化，監控 {currency_pair}，閾值 {threshold_percent}%")
    
    def make_decision(self, market_data):
        """
        根據市場數據決定是否交易
        
        Args:
            market_data: 市場數據字典，包含各貨幣對的最新匯率
            
        Returns:
            dict: 交易決策，包含是否交易、交易類型、貨幣對等
        """
        # 檢查是否有我們感興趣的貨幣對數據
        if self.currency_pair not in market_data:
            self.logger.warning(f"找不到 {self.currency_pair} 的數據")
            return {'should_trade': False}
        
        # 獲取當前匯率
        current_rate = market_data[self.currency_pair]['rate']
        
        # 如果這是第一次檢查，記錄匯率並返回不交易
        if self.previous_rate is None:
            self.previous_rate = current_rate
            self.logger.info(f"首次檢查 {self.currency_pair}，匯率為 {current_rate}")
            return {'should_trade': False}
        
        # 計算價格變化百分比
        percent_change = ((current_rate - self.previous_rate) / self.previous_rate) * 100
        
        # 記錄價格變化
        self.logger.info(f"{self.currency_pair} 匯率從 {self.previous_rate} 變為 {current_rate}，變化 {percent_change:.2f}%")
        
        # 決定是否交易
        if percent_change <= -self.threshold_percent:
            # 價格下跌超過閾值，買入
            decision = {
                'should_trade': True,
                'action': 'buy',
                'currency': self.currency_pair,
                'amount': self.trade_amount,
                'price': current_rate,
                'reason': f"{self.currency_pair} 價格下跌 {abs(percent_change):.2f}%，超過閾值 {self.threshold_percent}%"
            }
            self.logger.info(f"決定買入 {self.currency_pair}")
        elif percent_change >= self.threshold_percent:
            # 價格上漲超過閾值，賣出
            decision = {
                'should_trade': True,
                'action': 'sell',
                'currency': self.currency_pair,
                'amount': self.trade_amount,
                'price': current_rate,
                'reason': f"{self.currency_pair} 價格上漲 {percent_change:.2f}%，超過閾值 {self.threshold_percent}%"
            }
            self.logger.info(f"決定賣出 {self.currency_pair}")
        else:
            # 價格變化不足，不交易
            decision = {
                'should_trade': False
            }
            self.logger.debug(f"價格變化 {percent_change:.2f}% 不足以觸發交易")
        
        # 更新之前的匯率
        self.previous_rate = current_rate
        
        return decision
    
    def set_parameters(self, currency_pair=None, threshold_percent=None, trade_amount=None):
        """
        更新策略參數
        
        Args:
            currency_pair: 貨幣對
            threshold_percent: 閾值百分比
            trade_amount: 交易金額
        """
        if currency_pair:
            self.currency_pair = currency_pair
        
        if threshold_percent is not None:
            self.threshold_percent = threshold_percent
        
        if trade_amount is not None:
            self.trade_amount = trade_amount
        
        self.logger.info(f"策略參數已更新：貨幣對={self.currency_pair}，閾值={self.threshold_percent}%，交易金額={self.trade_amount}")


# 使用示例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 創建策略
    strategy = SimpleStrategy(currency_pair="EUR/USD", threshold_percent=0.3)
    
    # 模擬市場數據
    market_data_day1 = {
        "EUR/USD": {"rate": 1.1000, "timestamp": datetime.now().isoformat()}
    }
    
    # 第一次決策（應該不會交易，因為沒有之前的數據）
    decision1 = strategy.make_decision(market_data_day1)
    print(f"決策1: {decision1}")
    
    # 模擬第二天市場數據（價格下跌0.5%）
    market_data_day2 = {
        "EUR/USD": {"rate": 1.0945, "timestamp": datetime.now().isoformat()}
    }
    
    # 第二次決策（應該買入，因為價格下跌超過閾值）
    decision2 = strategy.make_decision(market_data_day2)
    print(f"決策2: {decision2}") 