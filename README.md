# AFTC - 自動外幣交易系統
Automatic Foreign Currency Transactions (外幣自動交易系統)

## 這是什麼？
這是一個幫助你自動買賣外幣的工具箱。
就像一個聰明的機器人，它可以根據你設定的規則自動決定何時買入或賣出外幣。

## 如何開始使用？
1. 安裝需要的工具：`pip install -r requirements.txt`
2. 設定你的交易API密鑰（在`config.py`中）
3. 選擇一個策略（在`strategies`資料夾中）
4. 執行`python main.py`開始交易

## 資料夾說明
- `core/`: 系統的「心臟」，負責數據和交易執行
- `strategies/`: 不同的交易策略（決定何時買賣）
- `tests/`: 測試系統是否正常運作

## 初學者指南
如果你是第一次使用，請先閱讀`docs/beginner_guide.md`
