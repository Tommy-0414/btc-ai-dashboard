import os
import requests
import google.generativeai as genai
from supabase import create_client, Client

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

genai.configure(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. 抓取熱門加密新聞
def fetch_crypto_news(symbol="BTC"):
    try:
        url = f"https://min-api.cryptocompare.com/data/v2/news/?categories={symbol}&excludeCategories=Sponsored"
        res = requests.get(url, timeout=10).json()
        news_items = res.get("Data", [])[:5]
        
        news_text = ""
        for i, news in enumerate(news_items, 1):
            title = news.get("title", "")
            source = news.get("source_info", {}).get("name", "加密媒體")
            news_text += f"{i}. [{source}] {title}\n"
        return news_text if news_text else "暫無重大新聞事件。"
    except Exception as e:
        print(f"抓取新聞失敗: {e}")
        return "新聞數據讀取失敗，僅針對技術面分析。"

# 2. 抓取行情數據
def fetch_market_data(symbol="BTC"):
    pair = "BTCUSDT" if symbol == "BTC" else "ETHUSDT"
    res = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}").json()
    return {
        "price": float(res["lastPrice"]),
        "high": float(res["highPrice"]),
        "low": float(res["lowPrice"]),
        "change": float(res["priceChangePercent"])
    }

# 3. 生成包含新聞佐證的 AI 分析
def generate_analysis(symbol="BTC"):
    data = fetch_market_data(symbol)
    news = fetch_crypto_news(symbol)
    name = "比特幣 (BTC)" if symbol == "BTC" else "乙太幣 (ETH)"
    
    prompt = f"""
    你是一位資深加密貨幣分析師，請針對【{name}】進行綜合分析。

    【市場數據】：
    - 當前價格：${data['price']} USDT
    - 24H最高 / 最低：${data['high']} / ${data['low']} USDT
    - 24H漲跌幅：{data['change']}%

    【最新市場新聞摘要】：
    {news}

    請嚴格依照以下三個標題輸出報告：

    【技術面與趨勢解讀】
    （分析價格支撐位與壓力位）

    【新聞消息面佐證】
    （請明確引用上方提供的新聞標題與來源，分析該新聞對 {symbol} 是利多還是利空）

    【操作建議與風險提示】
    （提供建議與止損點提示）
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text

def main():
    for symbol in ["BTC", "ETH"]:
        print(f"正在分析 {symbol}...")
        summary = generate_analysis(symbol)
        
        # 存入 Supabase，需確保資料表包含 symbol 欄位
        supabase.table("btc_analysis").insert({
            "symbol": symbol,
            "summary": summary
        }).execute()
        print(f"{symbol} 寫入成功！")

if __name__ == "__main__":
    main()
