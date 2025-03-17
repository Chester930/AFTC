"""
相關性交易策略 - 基於貨幣對之間的相關性進行交易
就像觀察不同書籍的暢銷趨勢，發現關聯後一起借閱
"""

import logging
import numpy as np
from datetime import datetime, timedelta

# 導入歷史數據管理器
from core.database.historical_data import HistoricalDataManager


class CorrelationStrategy:
    """
    相關性交易策略 - 利用貨幣對之間的相關性進行交易
    
    策略概念：
    1. 監控多個貨幣對之間的相關性
    2. 當觀察到兩個通常高度相關的貨幣對突然出現背離時
    3. 預期它們會恢復相關性，所以交易較弱的那一個
    """
    
    def __init__(self, primary_pair="EUR/USD", secondary_pairs=None, correlation_window=30, divergence_threshold=1.5, trade_amount=1000):
        """
        初始化相關性策略
        
        Args:
            primary_pair: 主要交易的貨幣對
            secondary_pairs: 用於比較的其他貨幣對
            correlation_window: 計算相關性的時間窗口（天數）
            divergence_threshold: 分歧閾值
            trade_amount: 交易金額
        """
        if secondary_pairs is None:
            secondary_pairs = ["GBP/USD", "AUD/USD"]
            
        self.primary_pair = primary_pair
        self.secondary_pairs = secondary_pairs
        self.correlation_window = correlation_window
        self.divergence_threshold = divergence_threshold
        self.trade_amount = trade_amount
        self.historical_data = HistoricalDataManager()
        self.logger = logging.getLogger('correlation_strategy')
        
        # 儲存過去的相關性數據
        self.historical_correlations = {}
        
        self.logger.info(f"相關性策略已初始化，主貨幣對: {primary_pair}，輔助貨幣對: {secondary_pairs}")
    
    def make_decision(self, market_data):
        """
        根據市場數據決定是否交易
        
        Args:
            market_data: 市場數據字典，包含各貨幣對的最新匯率
            
        Returns:
            dict: 交易決策，包含是否交易、交易類型、貨幣對等
        """
        # 檢查是否有主要貨幣對的數據
        if self.primary_pair not in market_data:
            self.logger.warning(f"找不到主要貨幣對 {self.primary_pair} 的數據")
            return {'should_trade': False}
        
        # 檢查是否有所有次要貨幣對的數據
        for pair in self.secondary_pairs:
            if pair not in market_data:
                self.logger.warning(f"找不到次要貨幣對 {pair} 的數據")
                return {'should_trade': False}
        
        # 計算當前的相關性和偏差
        divergence_data = self._calculate_divergence(market_data)
        
        # 如果沒有分歧數據，可能是首次運行或數據不足
        if not divergence_data:
            return {'should_trade': False}
        
        # 尋找最大分歧的貨幣對
        max_divergence_pair = None
        max_divergence_value = 0
        
        for pair, data in divergence_data.items():
            if abs(data['divergence']) > max_divergence_value:
                max_divergence_value = abs(data['divergence'])
                max_divergence_pair = pair
        
        # 如果最大分歧超過閾值，生成交易決策
        if max_divergence_value > self.divergence_threshold:
            divergence = divergence_data[max_divergence_pair]['divergence']
            correlation = divergence_data[max_divergence_pair]['correlation']
            
            # 決定交易方向
            # 如果分歧為正（主貨幣相對強勢），且相關性通常為正，賣出主貨幣
            # 如果分歧為負（主貨幣相對弱勢），且相關性通常為正，買入主貨幣
            if correlation > 0:
                action = 'sell' if divergence > 0 else 'buy'
            else:
                action = 'buy' if divergence > 0 else 'sell'
            
            primary_rate = market_data[self.primary_pair]['rate']
            
            decision = {
                'should_trade': True,
                'action': action,
                'currency': self.primary_pair,
                'amount': self.trade_amount,
                'price': primary_rate,
                'reason': f"{self.primary_pair} 與 {max_divergence_pair} 出現 {divergence:.2f} 的分歧，超過閾值 {self.divergence_threshold}，預期回歸"
            }
            
            self.logger.info(f"發現交易機會: {decision['reason']}")
            return decision
        
        # 沒有足夠大的分歧，不交易
        return {'should_trade': False}
    
    def _calculate_divergence(self, market_data):
        """
        計算當前市場相對於歷史相關性的分歧程度
        
        Args:
            market_data: 市場數據
            
        Returns:
            dict: 分歧數據
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=self.correlation_window*2)).strftime("%Y-%m-%d")
        
        # 獲取主貨幣對的歷史數據
        primary_data = self.historical_data.load_historical_data(self.primary_pair, start_date, end_date)
        
        if primary_data.empty:
            self.logger.warning(f"無法獲取 {self.primary_pair} 的歷史數據")
            return {}
        
        # 計算每個次要貨幣對的分歧
        divergence_data = {}
        
        for secondary_pair in self.secondary_pairs:
            # 獲取次要貨幣對的歷史數據
            secondary_data = self.historical_data.load_historical_data(secondary_pair, start_date, end_date)
            
            if secondary_data.empty:
                self.logger.warning(f"無法獲取 {secondary_pair} 的歷史數據")
                continue
            
            # 計算歷史相關性
            correlation = self.historical_data.get_correlation(
                self.primary_pair, secondary_pair, 
                window=self.correlation_window, 
                start_date=start_date, end_date=end_date
            )
            
            # 獲取最新的相關性值
            latest_correlation = correlation.iloc[-1] if not correlation.empty else 0
            
            # 保存歷史相關性
            self.historical_correlations[secondary_pair] = latest_correlation
            
            # 獲取當前匯率
            primary_current = market_data[self.primary_pair]['rate']
            secondary_current = market_data[secondary_pair]['rate']
            
            # 獲取前一天的匯率（如果有）
            primary_prev = primary_data['rate'].iloc[-2] if len(primary_data) > 1 else primary_data['rate'].iloc[-1]
            secondary_prev = secondary_data['rate'].iloc[-2] if len(secondary_data) > 1 else secondary_data['rate'].iloc[-1]
            
            # 計算百分比變化
            primary_change = (primary_current - primary_prev) / primary_prev
            secondary_change = (secondary_current - secondary_prev) / secondary_prev
            
            # 計算分歧 (兩種變化之間的差異，考慮相關性方向)
            # 如果相關性為正，它們應該同向變化；如果為負，它們應該反向變化
            expected_secondary_change = primary_change * latest_correlation
            divergence = primary_change - (secondary_change * np.sign(latest_correlation))
            
            self.logger.debug(f"{self.primary_pair} 變化: {primary_change:.4f}, {secondary_pair} 變化: {secondary_change:.4f}, 相關性: {latest_correlation:.2f}, 分歧: {divergence:.4f}")
            
            divergence_data[secondary_pair] = {
                'correlation': latest_correlation,
                'primary_change': primary_change,
                'secondary_change': secondary_change,
                'divergence': divergence
            }
        
        return divergence_data


# 使用示例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 創建策略
    strategy = CorrelationStrategy(
        primary_pair="EUR/USD",
        secondary_pairs=["GBP/USD", "AUD/USD"],
        correlation_window=30,
        divergence_threshold=0.01
    )
    
    # 模擬市場數據 (假設通常高度相關的歐元和英鎊出現分歧)
    market_data = {
        "EUR/USD": {"rate": 1.1000, "timestamp": datetime.now().isoformat()},
        "GBP/USD": {"rate": 1.2500, "timestamp": datetime.now().isoformat()},  # 通常與歐元高度正相關
        "AUD/USD": {"rate": 0.7100, "timestamp": datetime.now().isoformat()}
    }
    
    # 決策
    decision = strategy.make_decision(market_data)
    print(f"決策: {decision}")
    
    # 註：在真實環境中，這個策略需要足夠的歷史數據才能有效工作 