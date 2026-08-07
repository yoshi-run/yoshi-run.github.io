import json
import time
import pandas as pd
import yfinance as yf

# 追蹤清單
WATCHLIST = [
    {"name": "AAPL (蘋果)", "symbol": "AAPL", "type": "US"},
    {"name": "NVDA (輝達)", "symbol": "NVDA", "type": "US"},
    {"name": "MSFT (微軟)", "symbol": "MSFT", "type": "US"},
    {"name": "TSLA (特斯拉)", "symbol": "TSLA", "type": "US"},
    {"name": "AMZN (亞馬遜)", "symbol": "AMZN", "type": "US"},
    {"name": "2330 (台積電)", "symbol": "2330.TW", "type": "TW"},
    {"name": "2454 (聯發科)", "symbol": "2454.TW", "type": "TW"},
]


def fetch_financials(symbol, is_tw):
  try:
    stock = yf.Ticker(symbol)
    financials = stock.quarterly_financials
    cashflow = stock.quarterly_cashflow

    if financials is None or financials.empty:
      print(f"⚠️ 無法取得 {symbol} 的財報數據 (空白)")
      return []

    cols = list(financials.columns)[::-1]
    data = []

    for date in cols:
      q_date = date.strftime("%Y-%m")

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
        # 關鍵防護：必須確認 df 存在且該欄位 (col) 真的存在於 df.columns 中
        if df is None or df.empty or col not in df.columns:
          return 0.0

        for k in keys:
          if k in df.index:
            try:
              val = df.loc[k, col]
              if pd.notna(val):
                return float(val)
            except Exception:
              pass
        return 0.0

      rev = get_val(financials, rev_keys, date)
      net_inc = get_val(financials, net_keys, date)
      op_cash = get_val(cashflow, cash_keys, date)

      divisor = 1e8 if is_tw else 1e6

      data.append({
          "date": q_date,
          "revenue": round(rev / divisor, 2),
          "net_income": round(net_inc / divisor, 2),
          "operating_cash_flow": round(op_cash / divisor, 2),
      })

    return data
  except Exception as e:
    print(f"❌ 抓取 {symbol} 時發生例外狀況: {e}")
    return []


def main():
  output_data = {
      "_config": {"watchlist": WATCHLIST},
      "stocks": {},
  }

  for item in WATCHLIST:
    symbol = item["symbol"]
    name = item["name"]
    is_tw = item["type"] == "TW"

    print(f"🚀 正在抓取財報數據: {name} ({symbol})...")
    financials = fetch_financials(symbol, is_tw)

    output_data["stocks"][name] = {
        "symbol": symbol,
        "type": item["type"],
        "unit": "億新台幣" if is_tw else "百萬美元",
        "financials": financials,
    }

  with open("stock_data.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

  print("✅ 財報數據更新完成！已寫入 stock_data.json")


if __name__ == "__main__":
  main()
