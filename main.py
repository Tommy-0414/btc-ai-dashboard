import os
import requests
from google import genai
from supabase import create_client, Client

# 讀取環境變數（金鑰安全儲存於系統中）
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# 初始化 API 客戶端
ai_client = genai.Client(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_btc_data():
    # 向 Binance API 抓取 24小時 BTC 價格與漲跌幅
    url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
    res = requests.get(url).json()
    return {
        "price": round(float(res['lastPrice']), 2),
        "price_change": round(float(res['priceChangePercent']), 2),
        "high": round(float(res['highPrice']), 2),
        "low": round(float(res['lowPrice']), 2)
    }

def analyze_with_ai(data):
    prompt = f"""
    你是一名客觀的加密貨幣市場分析師。根據以下即時數據進行簡短分析：
    - 比特幣 (BTC) 當前價格：${data['price']}
    - 24小時漲跌幅：{data['price_change']}%
    - 24小時最高價：${data['high']}
    - 24小時最低價：${data['low']}

    請輸出格式如下（請保持簡短，不要有額外開場白）：
    【市場趨勢】[看多 / 看空 / 觀望]
    【市場分析】兩句簡短客觀的行情說明。
    【風險提示】一句提醒觀測關鍵價位的警示。
    """
    
    response = ai_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    return response.text

if __name__ == "__main__":
    print("開始抓取 BTC 數據...")
    btc_data = get_btc_data()
    
    print("呼叫 Gemini AI 進行分析...")
    analysis_result = analyze_with_ai(btc_data)
    
    print("將分析結果存入 Supabase...")
    supabase.table("btc_analysis").insert({
        "price": btc_data["price"],
        "summary": analysis_result,
        "raw_data": btc_data
    }).execute()
    
    print("成功！分析已完成並寫入資料庫！")
