import yfinance as yf
import requests
import json
import pandas as pd

# 1. 設定你想追蹤的台美股清單
WATCHLIST_US = ['AAPL', 'NVDA', 'MSFT']  # 美股代號
WATCHLIST_TW = ['2330', '2454']         # 台股代號

def get_us_financials(ticker_symbol):
    """取得美股季度財報數據"""
    stock = yf.Ticker(ticker_symbol)
    financials = stock.quarterly_financials
    cashflow = stock.quarterly_cashflow
    
    data = []
    if not financials.empty:
        # 取最近 4 個季度
        for date in financials.columns[:4]:
            q_date = date.strftime('%Y-%m-%d')
            rev = financials.loc['Total Revenue', date] if 'Total Revenue' in financials.index else 0
            net_income = financials.loc['Net Income', date] if 'Net Income' in financials.index else 0
            op_cash = cashflow.loc['Operating Cash Flow', date] if 'Operating Cash Flow' in cashflow.index else 0
            
            data.append({
                "date": q_date,
                "revenue": float(rev) / 1e6,       # 單位：百萬美元
                "net_income": float(net_income) / 1e6,
                "operating_cash_flow": float(op_cash) / 1e6
            })
    return data

def get_tw_financials(stock_id):
    """取得台股季度財報數據 (使用 FinMind API)"""
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": "TaiwanStockFinancialStatements",
        "stock_id": stock_id,
        "start_date": "2023-01-01"
    }
    res = requests.get(url, params=params).json()
    df = pd.DataFrame(res.get("data", []))
    
    if df.empty:
        return []

    # 簡單進行資料透視與處理
    pivoted = df.pivot(index='date', columns='type', values='value').fillna(0)
    
    result = []
    for date, row in pivoted.tail(4).iterrows():
        result.append({
            "date": date,
            "revenue": float(row.get('Revenue', 0)) / 1e8, # 單位：億台幣
            "net_income": float(row.get('IncomeAfterTaxes', 0)) / 1e8,
            "operating_cash_flow": float(row.get('CashFlowsFromOperatingActivities', 0)) / 1e8
        })
    return result

# 2. 彙整資料並儲存為 stock_data.json
all_data = {}

for symbol in WATCHLIST_US:
    all_data[symbol] = {"type": "US", "financials": get_us_financials(symbol)}

for symbol in WATCHLIST_TW:
    all_data[symbol] = {"type": "TW", "financials": get_tw_financials(symbol)}

with open('stock_data.json', 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

print("財報數據更新完成！已寫入 stock_data.json")