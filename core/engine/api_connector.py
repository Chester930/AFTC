"""
API連接器 - 連接外部數據源和交易平台
就像圖書館與其他圖書館連接的電話
"""

import requests
import json
import time
import logging
from datetime import datetime


class APIConnector:
    """
    API連接器 - 負責與外部API溝通
    """
    
    def __init__(self, api_key="demo", api_secret="demo", base_url="https://api.example.com"):
        """
        初始化API連接器
        
        Args:
            api_key: API密鑰
            api_secret: API密碼
            base_url: API基礎網址
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.session = requests.Session()
        self.logger = logging.getLogger('api_connector')
        
        # 設定API請求頭
        self.session.headers.update({
            'Content-Type': 'application/json',
            'API-Key': self.api_key,
            'User-Agent': 'ForexTradingLibrary/1.0'
        })
        
        self.logger.info("API連接器已初始化")
    
    def get_exchange_rate(self, from_currency, to_currency):
        """
        獲取兩種貨幣之間的匯率
        
        Args:
            from_currency: 起始貨幣代碼 (例如: "USD")
            to_currency: 目標貨幣代碼 (例如: "JPY")
            
        Returns:
            float: 匯率
        """
        try:
            # 構建API請求URL
            endpoint = f"/v1/exchange_rate/{from_currency}/{to_currency}"
            url = self.base_url + endpoint
            
            # 發送請求
            response = self.session.get(url)
            response.raise_for_status()  # 如果請求失敗，拋出異常
            
            # 解析響應
            data = response.json()
            
            if 'rate' in data:
                return float(data['rate'])
            else:
                self.logger.error(f"無法從API響應中獲取匯率: {data}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"獲取匯率時發生錯誤: {e}")
            return None
    
    def get_historical_rates(self, currency_pair, start_date, end_date):
        """
        獲取歷史匯率數據
        
        Args:
            currency_pair: 貨幣對 (例如: "USD/JPY")
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            
        Returns:
            list: 歷史匯率數據列表
        """
        try:
            # 構建API請求
            endpoint = "/v1/historical_rates"
            url = self.base_url + endpoint
            
            params = {
                'currency_pair': currency_pair,
                'start_date': start_date,
                'end_date': end_date,
                'interval': 'daily'
            }
            
            # 發送請求
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # 解析響應
            data = response.json()
            
            return data.get('rates', [])
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"獲取歷史匯率時發生錯誤: {e}")
            return []
    
    def execute_trade(self, trade_details):
        """
        執行交易
        
        Args:
            trade_details: 交易詳細資訊的字典
                {
                    'action': 'buy' 或 'sell',
                    'currency': 貨幣對 (例如: "USD/JPY"),
                    'amount': 交易金額,
                    'price': 交易價格 (可選)
                }
                
        Returns:
            dict: 交易結果
        """
        if self.api_key == "demo":
            # 在演示模式下，我們只是模擬交易
            self.logger.info(f"【模擬交易】: {trade_details}")
            return {
                'success': True,
                'transaction_id': f"demo-{int(time.time())}",
                'timestamp': datetime.now().isoformat(),
                'details': trade_details
            }
        
        try:
            # 構建API請求
            endpoint = "/v1/trade"
            url = self.base_url + endpoint
            
            # 準備請求數據
            payload = {
                'action': trade_details['action'],
                'currency_pair': trade_details['currency'],
                'amount': trade_details['amount']
            }
            
            if 'price' in trade_details:
                payload['price'] = trade_details['price']
            
            # 發送請求
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            # 解析響應
            result = response.json()
            
            self.logger.info(f"交易成功執行: {result['transaction_id']}")
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"執行交易時發生錯誤: {e}")
            return {'success': False, 'error': str(e)}
    
    def close(self):
        """關閉API連接"""
        self.session.close()
        self.logger.info("API連接已關閉")


# 使用示例
if __name__ == "__main__":
    # 簡單的測試代碼
    api = APIConnector()
    rate = api.get_exchange_rate("USD", "JPY")
    print(f"當前 USD/JPY 匯率: {rate}") 