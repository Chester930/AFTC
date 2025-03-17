# 就像圖書館的新書展示架
# 每分鐘自動更新最新歐元匯率 📈
# 使用方法：隨時來看最新匯率數字

import threading
import time
import logging
import json
import os
from datetime import datetime

# 導入API連接器
from core.engine.api_connector import APIConnector


class RealtimeDataManager:
    """
    即時數據管理器 - 負責獲取和存儲即時匯率數據
    就像是圖書館的新書展示架，展示最新的圖書（匯率）
    """
    
    def __init__(self, api_key="demo", update_interval=60):
        """
        初始化即時數據管理器
        
        Args:
            api_key: API密鑰，用於連接外部數據源
            update_interval: 更新間隔（秒）
        """
        self.api_connector = APIConnector(api_key=api_key)
        self.update_interval = update_interval
        self.currency_pairs = ["EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "USD/CAD"]
        self.latest_data = {}
        self.data_lock = threading.Lock()
        self.update_thread = None
        self.stop_flag = threading.Event()
        self.logger = logging.getLogger('realtime_data')
        
        # 確保數據目錄存在
        os.makedirs('data', exist_ok=True)
        
        self.logger.info("即時數據管理器已初始化")
        
        # 立即更新一次數據
        self._update_data()
        
        # 啟動定期更新線程
        self.start_updates()
    
    def start_updates(self):
        """開始定期更新數據"""
        if self.update_thread is None or not self.update_thread.is_alive():
            self.stop_flag.clear()
            self.update_thread = threading.Thread(target=self._update_loop)
            self.update_thread.daemon = True
            self.update_thread.start()
            self.logger.info(f"開始定期更新數據（每{self.update_interval}秒）")
    
    def stop_updates(self):
        """停止定期更新數據"""
        if self.update_thread and self.update_thread.is_alive():
            self.stop_flag.set()
            self.update_thread.join(timeout=2)
            self.logger.info("已停止更新數據")
    
    def _update_loop(self):
        """數據更新循環"""
        while not self.stop_flag.is_set():
            try:
                self._update_data()
                time.sleep(self.update_interval)
            except Exception as e:
                self.logger.error(f"更新數據時發生錯誤: {e}")
                time.sleep(5)  # 錯誤後稍微等待一下再重試
    
    def _update_data(self):
        """更新所有貨幣對的匯率數據"""
        updated_data = {}
        timestamp = datetime.now().isoformat()
        
        for pair in self.currency_pairs:
            from_currency, to_currency = pair.split('/')
            rate = self.api_connector.get_exchange_rate(from_currency, to_currency)
            
            if rate is not None:
                updated_data[pair] = {
                    'rate': rate,
                    'timestamp': timestamp
                }
                self.logger.debug(f"更新匯率: {pair} = {rate}")
            else:
                self.logger.warning(f"無法獲取匯率: {pair}")
        
        # 更新數據（使用鎖確保線程安全）
        with self.data_lock:
            self.latest_data = updated_data
        
        # 保存數據
        self._save_data_to_file(updated_data)
    
    def _save_data_to_file(self, data):
        """將數據保存到文件"""
        try:
            filename = f"data/realtime_{datetime.now().strftime('%Y%m%d')}.json"
            
            # 如果文件存在，先讀取已有數據
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    existing_data = json.load(f)
            else:
                existing_data = []
            
            # 添加新數據
            record = {
                'timestamp': datetime.now().isoformat(),
                'rates': data
            }
            existing_data.append(record)
            
            # 保存回文件
            with open(filename, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存數據到文件時發生錯誤: {e}")
    
    def get_latest_data(self):
        """獲取最新的匯率數據"""
        with self.data_lock:
            return self.latest_data.copy()
    
    def get_latest_rate(self, currency_pair):
        """
        獲取特定貨幣對的最新匯率
        
        Args:
            currency_pair: 貨幣對 (例如: "EUR/USD")
            
        Returns:
            float: 匯率，如果沒有數據則返回None
        """
        with self.data_lock:
            if currency_pair in self.latest_data:
                return self.latest_data[currency_pair]['rate']
            return None
    
    def close(self):
        """關閉數據管理器"""
        self.stop_updates()
        self.api_connector.close()
        self.logger.info("即時數據管理器已關閉")


# 使用示例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = RealtimeDataManager()
    
    # 等待一些數據收集
    time.sleep(5)
    
    # 顯示最新數據
    data = manager.get_latest_data()
    for pair, info in data.items():
        print(f"{pair}: {info['rate']}")
    
    # 關閉管理器
    manager.close() 