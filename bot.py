import requests
import time
import json
from datetime import datetime, timedelta

TOKEN = "8740187471:AAFnbyytjPdyfudWHubh0vfu9SRpOXdna0w" 
CHAT_ID = "1030427227"

# 🧠 daha akıllı duplicate kontrol
sent_markets = {}  # {market_id: {"side": "BUY/SELL", "time": datetime}}

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except Exception as e:
        print("Telegram HATA:", e)


def get_markets():
    url = "https://gamma-api.polymarket.com/markets"

    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception as e:
        print("API HATA:", e)
        return []


# 🧠 duplicate + direction cooldown
def is_duplicate(market_id, side, cooldown_minutes=30):

    if market_id not in sent_markets:
        return False

    data = sent_markets[market_id]

    # aynı direction ise blok
    if data["side"] == side:
        if datetime.utcnow() - data["time"] < timedelta(minutes=cooldown_minutes):
            return True

    return False


def update_sent(market_id, side):
    sent_markets[market_id] = {
        "side": side,
        "time": datetime.utcnow()
    }


def generate_signal(market):

    title = market.get("question", "No title")
    market_id = market.get("id")

    prices = market.get("outcomePrices")
    if not prices:
        return None, None

    try:
        prices = json.loads(prices)
        yes_price = float(prices[0])
    except:
        return None, None

    volume = float(market.get("volumeNum", 0))
    liquidity = float(market.get("liquidityNum", 0))

    # 🔥 kalite filtresi
    if volume < 50000 or liquidity < 10000:
        return None, None

    # 🧠 confidence (daha dengeli)
    volume_score = min(volume / 200000, 1) * 40
    liquidity_score = min(liquidity / 500000, 1) * 30
    edge_score = (0.5 - abs(yes_price - 0.5)) * 100

    confidence = int(volume_score + liquidity_score + edge_score)
    confidence = max(5, min(confidence, 95))

    # 🟢 BUY
    if yes_price <= 0.40:
        msg = f"""
🚨 POLY SİNYAL UYARISI 🚨

📌 {title}

🆔 Market ID: {market_id}

🟢 AL SİNYALİ

💰 Giriş: {round(yes_price, 2)} - {round(yes_price + 0.03, 2)}

🎯 Güven: {confidence}%

📊 Hacim: {int(volume):,}
💧 Likidite: {int(liquidity):,}

⚡ Momentum / akıllı para tespit edildi.

#Polymarket
"""
        return msg, "BUY"

    # 🔴 SELL
    if yes_price >= 0.60:
        msg = f"""
🚨 POLY SİNYAL UYARISI 🚨

📌 {title}

🆔 Market ID: {market_id}

🔴 SAT SİNYALİ

💰 Çıkış: {round(yes_price, 2)} - {round(yes_price - 0.03, 2)}

🎯 Güven: {confidence}%

📊 Hacim: {int(volume):,}
💧 Likidite: {int(liquidity):,}

⚠️ Aşırı fiyatlanma tespit edildi.

#Polymarket
"""
        return msg, "SELL"

    return None, None


while True:

    print("Scanning markets...")

    markets = get_markets()

    if not markets:
        time.sleep(10)
        continue

    for market in markets:

        market_id = market.get("id")
        if not market_id:
            continue

        signal, side = generate_signal(market)

        if signal:

            # 🧠 DUPLICATE CHECK
            if is_duplicate(market_id, side):
                print(f"SKIP DUPLICATE: {market_id} {side}")
                continue

            send(signal)

            print(f"SİNYAL GÖNDERİLDİ -> {market_id} ({side})")

            update_sent(market_id, side)

    time.sleep(10)
