import os
import time
import requests
from google import genai
from supabase import create_client, Client

# 1. 初始化環境變數與新版 SDK Client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. 直接串接動區動趨 (BlockTempo) WordPress REST API 抓取最新中文加密與總經新聞
def fetch_crypto_news(symbol="BTC"):
    news_text = ""
    try:
        # 透過 WordPress API 抓取動區最新文章（預抓 5 篇）
        url = "https://www.blocktempo.com/wp-json/wp/v2/posts?per_page=5"
        res = requests.get(url, timeout=10)
        
        if res.status_code == 200:
            posts = res.json()
            for i, post in enumerate(posts, 1):
                # WordPress API 的標題通常存在 rendered 欄位裡，並包含 HTML entity 需要簡單處理
                title = post.get("title", {}).get("rendered", "")
                # 簡單清理 HTML 標籤（若有）
                title = title.replace("&#8211;", "-").replace("&#8220;", "\"").replace("&#8221;", "\"")
                news_text += f"{i. [動區動趨] {title}\n"
    except Exception as e:
        print(f"抓取動區新聞失敗: {e}")

    return news_text if news_text else "暫無重大新聞事件，請依技術面與總體市場氣氛為主。"

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

# 4. 生成 AI 分析 (結合動區新聞與即時行情)
def generate_analysis(symbol="BTC"):
    data = fetch_market_data(symbol)
    news = fetch_crypto_news(symbol)
    name = "比特幣 (BTC)" if symbol == "BTC" else "乙太幣 (ETH)"
    
    prompt = f"""
    你是一位資深加密貨幣與總體經濟分析師，請針對【{name}】進行綜合分析。

    【市場即時數據】：
    - 當前價格：${data['price']} USD
    - 24H漲跌幅：{data['change']}%
    - 24H成交量：{data['volume']}

    【動區動趨 (BlockTempo) 最新頭條新聞】：
    {news}

    請特別注意：請務必將上方動區報導中的總經局勢、監管政策或突發事件（如川普動向、地緣政治、宏觀經濟等）納入新聞消息面佐證進行深度解讀。

    請嚴格依照以下三個區塊輸出報告（切勿使用任何星號 * 或 Markdown 符號）：

    【技術面與趨勢解讀】
    （分析當前價格區間、支撐位與壓力位）

    【新聞消息面佐證】
    （明確引用上方動區新聞標題，分析其對 {symbol} 帶來的避險或拋售影響）

    【綜合操作建議與風險提示】
    （給出短中期操作建議與風險提示）
    """
    
    # 嘗試呼叫 API 2 次，遇到 429 自動冷卻 30 秒
    for attempt in range(1, 3):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            
            # 清理文字中的星號 (*)
            clean_text = response.text.replace('*', '') if response.text else ""
            return clean_text
            
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"⚠️ 觸發 Gemini API 額度限制 (429)，等待 30 秒重試 (第 {attempt} 次)...")
                time.sleep(30)
            else:
                print(f"API 呼叫失敗: {e}")
                break
                
    return f"【系統提示】目前 API 呼叫頻率過高，暫時觸發冷卻保護機制。當前價格：${data['price']} USD，24H漲跌：{data['change']}%。"

# 5. 主程式執行
def main():
    symbols = ["BTC", "ETH"]
    for idx, symbol in enumerate(symbols):
        print(f"正在分析 {symbol}...")
        summary = generate_analysis(symbol)
        
        try:
            supabase.table("btc_analysis").insert({
                "symbol": symbol,
                "summary": summary
            }).execute()
            print(f"{symbol} 分析數據成功寫入 Supabase！")
        except Exception as e:
            print(f"寫入 Supabase 失敗: {e}")
        
        if idx < len(symbols) - 1:
            print("⏳ 幣種切換冷卻 20 秒...")
            time.sleep(20)

if __name__ == "__main__":
    main()
