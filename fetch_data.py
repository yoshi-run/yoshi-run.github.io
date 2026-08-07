import json
import pandas as pd
import yfinance as yf

# 設定你想追蹤的台美股清單
# 美股直接填寫代號，台股後面要加 .TW（例如 2330.TW, 2454.TW）
WATCHLIST = {
    'AAPL': {'type': 'US', 'symbol': 'AAPL'},
    'NVDA': {'type': 'US', 'symbol': 'NVDA'},
    'MSFT': {'type': 'US', 'symbol': 'MSFT'},
    '2330 (台積電)': {'type': 'TW', 'symbol': '2330.TW'},
    '2454 (聯發科)': {'type': 'TW', 'symbol': '2454.TW'},
}


def get_stock_financials(display_name, info):
  ticker_symbol = info['symbol']
  is_tw = info['type'] == 'TW'
  stock = yf.Ticker(ticker_symbol)

  financials = stock.quarterly_financials
  cashflow = stock.quarterly_cashflow

  data = []
  if not financials.empty:
    # 取得最近 4 個季度 (預設由新到舊，反轉成由舊到新)
    dates = list(financials.columns[:4])[::-1]

    for date in dates:
      q_date = date.strftime('%Y-%m-%d')
      rev = (
          financials.loc['Total Revenue', date]
          if 'Total Revenue' in financials.index
          else 0
      )
      net_inc = (
          financials.loc['Net Income', date]
          if 'Net Income' in financials.index
          else 0
      )
      op_cash = (
          cashflow.loc['Operating Cash Flow', date]
          if 'Operating Cash Flow' in cashflow.index
          else 0
      )

      # 台股除以 1億 (億台幣)，美股除以 100萬 (百萬美元)
      divisor = 1e8 if is_tw else 1e6

      data.append({
          'date': q_date,
          'revenue': round(float(rev) / divisor, 2),
          'net_income': round(float(net_inc) / divisor, 2),
          'operating_cash_flow': round(float(op_cash) / divisor, 2),
      })
  return data


all_data = {}
for display_name, info in WATCHLIST.items():
  print(f'正在抓取: {display_name} ({info["symbol"]})...')
  financials = get_stock_financials(display_name, info)
  if financials:
    all_data[display_name] = {
        'type': info['type'],
        'unit': '億新台幣' if info['type'] == 'TW' else '百萬美元',
        'financials': financials,
    }

with open('stock_data.json', 'w', encoding='utf-8') as f:
  json.dump(all_data, f, ensure_ascii=False, indent=2)

print('財報數據更新完成！已寫入 stock_data.json')
