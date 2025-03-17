"""
交易機器人 - 自動執行買賣決策
就像是圖書館的自動借還書機器
"""

import logging
import time
from datetime import datetime


class TradingBot:
    """
    交易機器人 - 自動執行買賣決策
    """
    
    def __init__(self, data_manager, strategy, trade_mode="paper"):
        """
        初始化交易機器人
        
        Args:
            data_manager: 數據管理器，用來取得匯率數據
            strategy: 交易策略，決定何時買賣
            trade_mode: 交易模式，"paper"表示只是模擬不真的花錢
        """
        self.data_manager = data_manager
        self.strategy = strategy
        self.trade_mode = trade_mode
        self.is_running = False
        self.trade_history = []
        
        # 設定日誌
        logging.basicConfig(
            filename='trading.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('trading_bot')
        self.logger.info("交易機器人已初始化")
    
    def check_and_execute(self):
        """
        檢查市場狀況並執行交易
        這就像是機器人定期巡視書架，看看是否有書要借出或歸還
        """
        try:
            # 1. 取得最新的匯率數據
            current_data = self.data_manager.get_latest_data()
            
            # 2. 使用策略決定是否要交易
            decision = self.strategy.make_decision(current_data)
            
            # 3. 根據決策執行交易
            if decision['should_trade']:
                self._execute_trade(decision)
            else:
                self.logger.info("目前無交易機會")
                
            return True
        except Exception as e:
            self.logger.error(f"交易過程發生錯誤: {str(e)}")
            return False
    
    def _execute_trade(self, decision):
        """
        執行交易決策
        
        Args:
            decision: 包含交易詳情的字典
        """
        # 記錄交易
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'action': decision['action'],  # 'buy' 或 'sell'
            'currency': decision['currency'],
            'amount': decision['amount'],
            'price': decision['price'],
            'reason': decision['reason']
        }
        
        # 如果是真實交易模式，則實際執行交易
        if self.trade_mode == "live":
            self.logger.info(f"執行{decision['action']}交易: {decision['amount']} {decision['currency']} @ {decision['price']}")
            # 這裡會連接到實際的交易API
            # api_connector.execute_trade(decision)
        else:
            self.logger.info(f"【模擬】{decision['action']}交易: {decision['amount']} {decision['currency']} @ {decision['price']}")
        
        # 將交易記錄添加到歷史記錄
        self.trade_history.append(trade_record)
        
        # 顯示交易資訊
        direction = "買入" if decision['action'] == 'buy' else "賣出"
        print(f"【{self.trade_mode}】{direction} {decision['amount']} {decision['currency']} @ {decision['price']}")
        print(f"原因: {decision['reason']}")
    
    def get_trade_history(self):
        """獲取交易歷史記錄"""
        return self.trade_history
    
    def shutdown(self):
        """關閉交易機器人"""
        self.logger.info("交易機器人關閉中...")
        self.is_running = False
        # 進行必要的清理工作
        self.data_manager.close()
        self.logger.info("交易機器人已安全關閉")
        return True 