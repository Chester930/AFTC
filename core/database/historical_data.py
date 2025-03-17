# 就像圖書館的歷史檔案室
# 這裡存放過去10年的美元匯率紀錄 📚
# 使用方法：查詢某天匯率就像查閱歷史檔案

import os
import json
import pandas as pd
import logging
from datetime import datetime, timedelta

# 導入API連接器
from core.engine.api_connector import APIConnector


class HistoricalDataManager:
    """
    歷史數據管理器 - 負責存儲和分析歷史匯率數據
    就像是圖書館的歷史檔案室，存放過去所有的圖書記錄（匯率歷史）
    """
    
    def __init__(self, data_dir="data/historical"):
        """
        初始化歷史數據管理器
        
        Args:
            data_dir: 歷史數據存儲目錄
        """
        self.data_dir = data_dir
        self.api_connector = APIConnector()
        self.logger = logging.getLogger('historical_data')
        
        # 確保數據目錄存在
        os.makedirs(data_dir, exist_ok=True)
        
        self.logger.info("歷史數據管理器已初始化")
    
    def load_historical_data(self, currency_pair, start_date=None, end_date=None):
        """
        載入歷史匯率數據
        
        Args:
            currency_pair: 貨幣對 (例如: "USD/JPY")
            start_date: 開始日期 (YYYY-MM-DD)，如果為None則從最早可用數據開始
            end_date: 結束日期 (YYYY-MM-DD)，如果為None則到最新數據
            
        Returns:
            pandas.DataFrame: 歷史數據，包含日期和匯率
        """
        # 檢查本地是否有數據
        local_data = self._load_local_data(currency_pair)
        
        # 如果沒有本地數據，或者需要更新，從API獲取
        if local_data.empty or self._need_update(local_data, currency_pair):
            self.update_historical_data(currency_pair)
            local_data = self._load_local_data(currency_pair)
        
        # 過濾日期範圍
        if start_date:
            local_data = local_data[local_data.index >= start_date]
        if end_date:
            local_data = local_data[local_data.index <= end_date]
        
        return local_data
    
    def _load_local_data(self, currency_pair):
        """從本地文件載入數據"""
        file_path = os.path.join(self.data_dir, f"{currency_pair.replace('/', '_')}.json")
        
        if not os.path.exists(file_path):
            return pd.DataFrame(columns=["date", "rate"]).set_index("date")
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # 轉換為DataFrame
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
            return df
            
        except Exception as e:
            self.logger.error(f"載入本地數據時發生錯誤: {e}")
            return pd.DataFrame(columns=["date", "rate"]).set_index("date")
    
    def _need_update(self, local_data, currency_pair):
        """檢查是否需要更新數據"""
        if local_data.empty:
            return True
        
        # 檢查最新數據日期
        latest_date = local_data.index.max()
        today = datetime.now().date()
        
        # 如果最新數據是昨天或更早，需要更新
        return latest_date.date() < today - timedelta(days=1)
    
    def update_historical_data(self, currency_pair):
        """更新歷史數據"""
        try:
            # 檢查現有數據
            local_data = self._load_local_data(currency_pair)
            
            # 確定需要獲取的日期範圍
            if local_data.empty:
                # 如果沒有數據，獲取過去5年數據
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=5*365)).strftime("%Y-%m-%d")
            else:
                # 獲取最新日期到現在的數據
                latest_date = local_data.index.max()
                start_date = (latest_date + timedelta(days=1)).strftime("%Y-%m-%d")
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            # 從API獲取數據
            self.logger.info(f"更新匯率數據: {currency_pair} 從 {start_date} 到 {end_date}")
            new_data = self.api_connector.get_historical_rates(currency_pair, start_date, end_date)
            
            if not new_data:
                self.logger.warning(f"未找到新數據: {currency_pair}")
                return
            
            # 轉換新數據格式
            new_df = pd.DataFrame(new_data)
            new_df["date"] = pd.to_datetime(new_df["date"])
            new_df = new_df.set_index("date")
            
            # 合併新舊數據
            if not local_data.empty:
                combined_data = pd.concat([local_data, new_df])
                combined_data = combined_data[~combined_data.index.duplicated(keep='last')]
            else:
                combined_data = new_df
            
            # 保存數據
            self._save_data(currency_pair, combined_data)
            self.logger.info(f"成功更新匯率數據: {currency_pair}")
            
        except Exception as e:
            self.logger.error(f"更新歷史數據時發生錯誤: {e}")
    
    def _save_data(self, currency_pair, data):
        """保存數據到文件"""
        file_path = os.path.join(self.data_dir, f"{currency_pair.replace('/', '_')}.json")
        
        # 重置索引，將日期轉為列
        df_to_save = data.reset_index()
        # 轉換日期為字符串
        df_to_save["date"] = df_to_save["date"].dt.strftime("%Y-%m-%d")
        
        # 保存為JSON
        with open(file_path, 'w') as f:
            json.dump(df_to_save.to_dict('records'), f, indent=2)
    
    def get_moving_average(self, currency_pair, window=30, start_date=None, end_date=None):
        """
        計算移動平均線
        
        Args:
            currency_pair: 貨幣對
            window: 窗口大小（天數）
            start_date: 開始日期
            end_date: 結束日期
            
        Returns:
            pandas.Series: 移動平均線
        """
        data = self.load_historical_data(currency_pair, start_date, end_date)
        return data["rate"].rolling(window=window).mean()
    
    def get_volatility(self, currency_pair, window=30, start_date=None, end_date=None):
        """
        計算波動率（標準差）
        
        Args:
            currency_pair: 貨幣對
            window: 窗口大小（天數）
            start_date: 開始日期
            end_date: 結束日期
            
        Returns:
            pandas.Series: 波動率
        """
        data = self.load_historical_data(currency_pair, start_date, end_date)
        return data["rate"].rolling(window=window).std()
    
    def get_correlation(self, currency_pair1, currency_pair2, window=30, start_date=None, end_date=None):
        """
        計算兩個貨幣對之間的相關性
        
        Args:
            currency_pair1: 第一個貨幣對
            currency_pair2: 第二個貨幣對
            window: 窗口大小（天數）
            start_date: 開始日期
            end_date: 結束日期
            
        Returns:
            pandas.Series: 相關性
        """
        data1 = self.load_historical_data(currency_pair1, start_date, end_date)
        data2 = self.load_historical_data(currency_pair2, start_date, end_date)
        
        # 確保日期一致
        common_dates = data1.index.intersection(data2.index)
        data1 = data1.loc[common_dates]
        data2 = data2.loc[common_dates]
        
        # 計算滾動相關性
        return data1["rate"].rolling(window=window).corr(data2["rate"])


# 使用示例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = HistoricalDataManager()
    
    # 載入過去1年的USD/JPY數據
    today = datetime.now().date()
    one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    data = manager.load_historical_data("USD/JPY", start_date=one_year_ago)
    
    # 顯示前5筆數據
    print(data.head())
    
    # 計算30天移動平均線
    ma30 = manager.get_moving_average("USD/JPY", window=30)
    print("\n30天移動平均線:")
    print(ma30.tail()) 