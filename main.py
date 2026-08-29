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

# 2. 抓取熱門加密新聞 (修復 slice 錯誤)
def fetch_crypto_news(symbol="BTC"):
    try:
        url = f"https://min-api.cryptocompare.com/data/v2/news/?categories={symbol}&excludeCategories=Sponsored"
        res = requests.get(url, timeout=10).json()
        news_data = res.get("Data", [])
        
        # 安全取前 5 則新聞
        news_items = news_data[:5] if isinstance(news_data, list) else []
        
        news_text = ""
        for i, news in enumerate(news_items, 1):
            if isinstance(news, dict):
                title = news.get("title", "")
                source = news.get("source_info", {}).get("name", "加密媒體")
                news_text += f"{i}. [{source}] {title}\n"
        return news_text if news_text else "暫無重大新聞事件。"
    except Exception as e:
        print(f"抓取新聞失敗: {e}")
        return "新聞數據讀取失敗，僅針對技術面分析。"

# 3. 抓取行情數據
def fetch_market_data(symbol="BTC"):
    coin_id = "bitcoin" if symbol == "BTC" else "ethereum"
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_vol=true&include_24hr_change=true"
        res = requests.get(url, timeout=10).json()
        
        data = res.get(coin_id, {})
        return {
            "price": data.get("usd", "暫無數據"),
            "change": round(data.get("usd_24h_change", 0.0), 2),
            "volume": round(data.get("usd_24h_vol", 0.0), 2)
        }
    except Exception as e:
        print(f"行情抓取失敗: {e}")
        return {
            "price": "請參考即時K線圖",
            "change": "波動中",
            "volume": "數據更新中"
        }

# 4. 生成 AI 分析 (修復 Gemini 模型路徑)
def generate_analysis(symbol="BTC"):
    data = fetch_market_data(symbol)
    news = fetch_crypto_news(symbol)
    name = "比特幣 (BTC)" if symbol == "BTC" else "乙太幣 (ETH)"
    
    prompt = f"""
    你是一位資深加密貨幣分析師，請針對【{name}】進行綜合分析。

    【市場即時數據】：
    - 當前價格：${data['price']} USD
    - 24H漲跌幅：{data['change']}%
    - 24H成交量：{data['volume']}

    【最新市場新聞摘要】：
    {news}

    請嚴格依照以下三個區塊輸出報告：

    【技術面與趨勢解讀】
    （分析當前價格區間、支撐位與壓力位）

    【新聞消息面佐證】
    （請明確引用上方【最新市場新聞摘要】中的新聞標題與來源，分析該新聞事件對 {symbol} 價格走勢帶來的正面或負面影響）

    【綜合操作建議與風險提示】
    （給出短中期操作建議與風險提示）
    """
    
    # 這裡直接傳入 'gemini-1.5-flash'（SDK 會自動處理前綴）
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        # 備用相容模型名稱
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text

# 5. 主程式執行
def main():
    for symbol in ["BTC", "ETH"]:
        print(f"正在分析 {symbol}...")
        summary = generate_analysis(symbol)
        
        supabase.table("btc_analysis").insert({
            "symbol": symbol,
            "summary": summary
        }).execute()
        print(f"{symbol} 分析完成並成功寫入 Supabase！")

if __name__ == "__main__":
    main()
