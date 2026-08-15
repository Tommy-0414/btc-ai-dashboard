import os
import requests
from google import genai
from supabase import create_client, Client

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

ai_client = genai.Client(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_btc_data():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&community_data=false&developer_data=false&sparkline=false"
    headers = {"accept": "application/json"}
    res = requests.get(url, headers=headers).json()
    
    market_data = res.get('market_data', {})
    
    return {
        "price": round(float(market_data['current_price']['usd']), 2),
        "price_change": round(float(market_data['price_change_percentage_24h']), 2),
        "high": round(float(market_data['high_24h']['usd']), 2),
        "low": round(float(market_data['low_24h']['usd']), 2),
        "ath": round(float(market_data['ath']['usd']), 2),
        "volume": round(float(market_data['total_volume']['usd']), 2)
    }

def analyze_with_ai(data):
    prompt = f"""
    你是一名高階加密貨幣量化分析師，請針對以下比特幣 (BTC) 即時行情數據進行專業且深入的市場簡報：
    - 即時價格：${data['price']} USDT
    - 24H 漲跌幅：{data['price_change']}%
    - 24H 最高價：${data['high']} USDT
    - 24H 最低價：${data['low']} USDT
    - 歷史最高價 (ATH)：${data['ath']} USDT
    - 24H 總交易量：${data['volume']:,} USDT

    請嚴格依照以下格式輸出報告（使用清晰標題與重點條列，字數約 200-300 字）：

    【市場定調與態勢】
    (說明目前市場屬於強勢多頭、震盪整理還是空頭修正，並給出建議觀望或佈局之看法)

    【關鍵價位分析】
    - 上方壓力位：估計區間
    - 下方支撐位：估計區間

    【深度行情解讀】
    (結合 24H 振幅與交易量，分析資金動向與市場情緒)

    【操作策略與風險提示】
    (針對短期與中長期交易者提出客觀的操作建議與停損概念)
    """
    
    response = ai_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    return response.text

if __name__ == "__main__":
    btc_data = get_btc_data()
    analysis_result = analyze_with_ai(btc_data)
    
    supabase.table("btc_analysis").insert({
        "price": btc_data["price"],
        "summary": analysis_result,
        "raw_data": btc_data
    }).execute()
    print("分析更新完成！")
