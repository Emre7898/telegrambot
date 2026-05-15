import requests
import time
import json
from datetime import datetime

TOKEN = "8740187471:AAFnbyytjPdyfudWHubh0vfu9SRpOXdna0w"
CHAT_ID = "1030427227"

sent_markets = {}
last_send_time = 0


def send(msg):
    global last_send_time

    # 🧠 burst limiter (Telegram spam engel)
    now = time.time()
    if now - last_send_time < 1.2:
        time.sleep(1.2 - (now - last_send_time))

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg
        })
        last_send_time = time.time()
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


def is_duplicate(market_id, side):
    if market_id not in sent_markets:
        return False

    if sent_markets[market_id] == side:
        return True

    return False


def mark_sent(market_id, side):
    sent_markets[market_id] = side


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

    if volume < 50000 or liquidity < 10000:
        return None, None

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

🟢 AL SİNYALİ

💰 Giriş: {round(yes_price, 2)} - {round(yes_price + 0.03, 2)}

🎯 Güven: {confidence}%

📊 Hacim: {int(volume):,}
💧 Likidite: {int(liquidity):,}

#Polymarket
"""
        return msg, "BUY"

    # 🔴 SELL
    if yes_price >= 0.60:
        msg = f"""
🚨 POLY SİNYAL UYARISI 🚨

📌 {title}

🔴 SAT SİNYALİ

💰 Çıkış: {round(yes_price, 2)} - {round(yes_price - 0.03, 2)}

🎯 Güven: {confidence}%

📊 Hacim: {int(volume):,}
💧 Likidite: {int(liquidity):,}

#Polymarket
"""
        return msg, "SELL"

    return None, None


while True:

    print("Scanning markets...")

    markets = get_markets()

    if not markets:
        time.sleep(5)
        continue

    for market in markets:

        market_id = market.get("id")
        if not market_id:
            continue

        signal, side = generate_signal(market)

        if signal:

            # 🧠 duplicate check
            if is_duplicate(market_id, side):
                continue

            # ⚡ ANINDA GÖNDER
            send(signal)

            print(f"SİNYAL GÖNDERİLDİ -> {market_id} ({side})")

            mark_sent(market_id, side)

            # 🔥 BURST ENGEL (kritik)
            time.sleep(1.5)

    # 🔄 daha “live feel”
    time.sleep(5)
