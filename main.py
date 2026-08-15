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
    headers = {"accept": "application/json", "Cache-Control": "no-cache"}
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
    你是一名高階加密貨幣量化交易分析師。請根據以下即時數據進行深度且詳盡的市場技術分析報告：
    - 即時價格：${data['price']} USDT
    - 24H 漲跌幅：{data['price_change']}%
    - 24H 最高價：${data['high']} USDT
    - 24H 最低價：${data['low']} USDT
    - 歷史最高價 (ATH)：${data['ath']} USDT
    - 24H 總交易量：${data['volume']:,} USDT

    排動與輸出格式要求：
    1. 絕對不要使用任何星號符號 (例如 ** 或 * )，避免出現亂碼與 Markdown 符號。
    2. 請直接使用以下定義好的文字區塊輸出報告：

    【多空方向評級】
    市場趨勢：[強勢看多 / 偏多看待 / 盤整觀望 / 偏空看待 / 強勢看空]
    短線策略：[建議逢低佈局 / 建議逢高減碼 / 建議觀望等待突破]

    【關鍵價位分析】
    上方強阻力位：估算價格與說明
    下方強支撐位：估算價格與說明

    【深度行情與技術解讀】
    詳細分析當前價格在 24H 波動區間內的位置、多空雙方力量拉鋸情形，以及交易量對當前趨勢的佐證程度（約 150-200 字）。

    【操作建議與風險提示】
    提供針對短期交易者與中長期持有者具體的入場思維、注意事項及嚴格的停損概念（約 100 字）。
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
    print(f"最新價格 ${btc_data['price']} 與詳細分析已寫入 Supabase！")
