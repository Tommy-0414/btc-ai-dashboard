import os
import requests
import google.generativeai as genai
from supabase import create_client, Client

# 1. 初始化環境變數
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

genai.configure(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. 抓取最新加密貨幣新聞的函式
def fetch_crypto_news(symbol="BTC"):
    try:
        # 使用 CryptoCompare 免費新聞 API
        url = f"https://min-api.cryptocompare.com/data/v2/news/?categories={symbol}&excludeCategories=Sponsored"
        res = requests.get(url, timeout=10).json()
        news_items = res.get("Data", [])[:5] # 取最新 5 則新聞
        
        news_text = ""
        for i, news in enumerate(news_items, 1):
            title = news.get("title", "")
            source = news.get("source_info", {}).get("name", "加密新聞")
            news_text += f"{i}. [{source}] {title}\n"
        return news_text if news_text else "暫無最新重大新聞。"
    except Exception as e:
        print(f"抓取新聞失敗 ({symbol}): {e}")
        return "新聞數據抓取失敗，依據技術面進行分析。"

# 3. 抓取即時價格與技術指標
def fetch_market_data(symbol="BTC"):
    # 這裡可以用你原本抓取 TradingView / Binance 價格的邏輯
    symbol_pair = "BTCUSDT" if symbol == "BTC" else "ETHUSDT"
    res = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol_pair}").json()
    return {
        "price": float(res["lastPrice"]),
        "high": float(res["highPrice"]),
        "low": float(res["lowPrice"]),
        "volume": float(res["volume"]),
        "change": float(res["priceChangePercent"])
    }

# 4. 生成 AI 分析報告 (含新聞佐證)
def generate_analysis(symbol="BTC"):
    market_data = fetch_market_data(symbol)
    news_data = fetch_crypto_news(symbol)
    
    coin_name = "比特幣 (BTC)" if symbol == "BTC" else "乙太幣 (ETH)"
    
    prompt = f"""
    你是一位專業的加密貨幣市場分析師。請針對【{coin_name}】進行綜合走勢分析。

    【市場即時數據】：
    - 當前價格：${market_data['price']} USDT
    - 24小時最高價：${market_data['high']} USDT
    - 24小時最低價：${market_data['low']} USDT
    - 24小時漲跌幅：{market_data['change']}%
    - 24小時成交量：{market_data['volume']}

    【最新市場重大新聞摘要】：
    {news_data}

    請輸出格式嚴謹的分析報告，必須包含以下三個區塊：
    
    【市場走勢與技術面評估】
    （說明當前價格位階、支撐與壓力區間）

    【消息面與新聞事件解讀】
    （重點！請結合上面提供的【最新市場重大新聞摘要】，具體分析這些新聞事件對 {symbol} 價格走勢帶來的正面或負面影響，讓讀者知道分析的依據）

    【綜合操作建議與風險提示】
    （給出短中期的操作建議與止損風險提示）
    """
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text

# 5. 執行分析並寫入 Supabase (分別記錄 BTC 與 ETH)
def main():
    for symbol in ["BTC", "ETH"]:
        print(f"正在分析 {symbol}...")
        summary = generate_analysis(symbol)
        
        # 寫入 Supabase (建議資料表新增 symbol 欄位，或個別更新)
        data = {
            "symbol": symbol, # 請確保 Supabase btc_analysis 資料表有 symbol 欄位 (預設可設 BTC)
            "summary": summary
        }
        supabase.table("btc_analysis").insert(data).execute()
        print(f"{symbol} 分析完成並已寫入 Supabase！")

if __name__ == "__main__":
    main()
