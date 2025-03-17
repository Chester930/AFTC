#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主程式入口 - 用來啟動交易機器人
就像是圖書館的開關門按鈕
"""

import os
import sys
import time
from configparser import ConfigParser

# 導入核心組件
from core.engine.trading_bot import TradingBot
from core.database.realtime_data import RealtimeDataManager

# 導入策略（這裡作為範例，實際使用時可透過設定檔指定）
from strategies.single_currency.simple_strategy import SimpleStrategy


def main():
    """
    主程式入口
    """
    print("====== 歡迎使用外幣自動交易系統 ======")
    print("系統正在啟動...")
    
    # 1. 載入設定檔
    config = ConfigParser()
    if os.path.exists('config.ini'):
        config.read('config.ini')
        print("✓ 已載入設定檔")
    else:
        print("⚠ 找不到設定檔，將使用預設設定")
        # 創建預設設定檔
        create_default_config()
        config.read('config.ini')
    
    # 2. 初始化數據管理器
    data_manager = RealtimeDataManager(
        api_key=config.get('API', 'key', fallback='demo'),
        update_interval=config.getint('Settings', 'update_interval', fallback=60)
    )
    print("✓ 數據管理器已啟動")
    
    # 3. 選擇交易策略
    strategy_name = config.get('Strategy', 'name', fallback='simple')
    if strategy_name == 'simple':
        strategy = SimpleStrategy()
        print("✓ 已選擇簡單交易策略")
    else:
        print("⚠ 未知的策略名稱，將使用簡單策略")
        strategy = SimpleStrategy()
    
    # 4. 啟動交易機器人
    bot = TradingBot(data_manager, strategy)
    print("✓ 交易機器人已啟動")
    print("====================================")
    
    try:
        # 5. 開始交易迴圈
        print("開始監控市場...")
        while True:
            bot.check_and_execute()
            time.sleep(config.getint('Settings', 'check_interval', fallback=300))
    except KeyboardInterrupt:
        print("\n使用者中斷程式")
    finally:
        print("系統正在關閉...")
        bot.shutdown()
        print("再見！")


def create_default_config():
    """創建預設設定檔"""
    config = ConfigParser()
    config['API'] = {
        'key': 'demo',
        'secret': 'demo'
    }
    config['Settings'] = {
        'update_interval': '60',  # 每60秒更新一次數據
        'check_interval': '300',  # 每5分鐘檢查一次交易機會
        'trade_mode': 'paper'     # 紙上交易模式，不會真的花錢
    }
    config['Strategy'] = {
        'name': 'simple',
        'currency': 'USD/JPY',
        'threshold': '0.5'        # 當價格變動超過0.5%時交易
    }
    
    with open('config.ini', 'w') as f:
        config.write(f)


if __name__ == "__main__":
    main() 