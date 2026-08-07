import json
import os
import time
import pandas as pd
import yfinance as yf

# 預設追蹤清單（若 stock_data.json 已有清單則優先讀取，支援網頁動態新增）
DEFAULT_STOCKS = [
    {"name": "AAPL (蘋果)", "symbol": "AAPL", "type": "US"},
    {"name": "NVDA (輝達)", "symbol": "NVDA", "type": "US"},
    {"name": "MSFT (微軟)", "symbol": "MSFT", "type": "US"},
    {"name": "2330 (台積電)", "symbol": "2330.TW", "type": "TW"},
    {"name": "2454 (聯發科)", "symbol": "2454.TW", "type": "TW"},
]


def load_stock_list():
  """從現有的 stock_data.json 讀取股票清單，若不存在則用預設值"""
  if os.path.exists("stock_data.json"):
    try:
      with open("stock_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        if "_config" in data and "watchlist" in data["_config"]:
          return data["_config"]["watchlist"]
    except Exception as e:
      print(f"讀取現有設定失敗: {e}")
  return DEFAULT_STOCKS


def fetch_financials(symbol, is_tw):
  """抓取個別股票財報數據（含重試機制）"""
  stock = yf.Ticker(symbol)

  # 重試機制
  financials = pd.DataFrame()
  cashflow = pd.DataFrame()
  for attempt in range(3):
    try:
      financials = stock.quarterly_financials
      cashflow = stock.quarterly_cashflow
      if not financials.empty:
        break
    except Exception:
      time.sleep(1)

  if financials.empty:
    print(f"⚠️ 無法取得 {symbol} 的財報數據")
    return []

  # 取得最近 4 個季度 (反轉為舊到新)
  cols = list(financials.columns[:4])[::-1]
  data = []

  for date in cols:
    q_date = date.strftime("%Y-%m-%d")

    # 嘗試多種可能性欄位名稱 (以防 Yahoo 欄位改名)
    rev_keys = ["Total Revenue", "Revenue", "Operating Revenue"]
    net_keys = [
        "Net Income",
        "Net Income Common Stockholders",
        "Net Income Including Noncontrolling Interests",
    ]
    cash_keys = [
        "Operating Cash Flow",
        "Cash Flow From Operating Activities",
        "Total Cash From Operating Activities",
    ]

    def get_val(df, keys, col):
      for k in keys:
        if k in df.index:
          val = df.loc[k, col]
          if pd.notna(val):
            return float(val)
      return 0.0

    rev = get_val(financials, rev_keys, date)
    net_inc = get_val(financials, net_keys, date)
    op_cash = get_val(cashflow, cash_keys, date)

    # 單位轉換：台股除以 1億 (億台幣)，美股除以 100萬 (百萬美元)
    divisor = 1e8 if is_tw else 1e6

    data.append({
        "date": q_date,
        "revenue": round(rev / divisor, 2),
        "net_income": round(net_inc / divisor, 2),
        "operating_cash_flow": round(op_cash / divisor, 2),
    })

  return data


def main():
  watchlist = load_stock_list()
  output_data = {
      "_config": {"watchlist": watchlist},
      "stocks": {},
  }

  for item in watchlist:
    symbol = item["symbol"]
    name = item["name"]
    is_tw = item["type"] == "TW"

    print(f"🚀 正在抓取: {name} ({symbol})...")
    financials = fetch_financials(symbol, is_tw)

    output_data["stocks"][name] = {
        "symbol": symbol,
        "type": item["type"],
        "unit": "億新台幣" if is_tw else "百萬美元",
        "financials": financials,
    }

  with open("stock_data.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

  print("✅ 所有財報數據更新完成！已寫入 stock_data.json")


if __name__ == "__main__":
  main()
