import random
import requests
import time

TOKEN = "8740187471:AAFnbyytjPdyfudWHubh0vfu9SRpOXdna0w"
CHAT_ID = "1030427227"

# Telegram mesaj gönderme
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

# Polymarket marketlerini çek
def get_markets():
    url = "https://gamma-api.polymarket.com/markets"

    try:
        r = requests.get(url)
        return r.json()

    except Exception as e:
        print("API HATA:", e)
        return []

# Sinyal üret
def generate_signal(market):

    title = market.get("question", "No title")

    prices = market.get("outcomePrices")

    if not prices:
        return None

    try:
        prices = eval(prices)
        yes_price = float(prices[0])
    except:
        return None

    volume = float(market.get("volumeNum", 0))
    liquidity = float(market.get("liquidityNum", 0))

    # düşük hacim filtre
    if volume < 50000:
        return None

    confidence = int(volume / 10000)

    if confidence > 95:
        confidence = 95

    # BUY SIGNAL
    if yes_price <= 0.40:

        return f"""
🚨 POLY SIGNAL ALERT 🚨

📌 {title}

🟢 BUY SIGNAL

💰 YES Price: {yes_price}
📊 Volume: {int(volume):,}
💧 Liquidity: {int(liquidity):,}

🔥 Momentum Building
📈 Market Oversold

🎯 Confidence: {confidence}%
"""

    # SELL SIGNAL
    if yes_price >= 0.60:

        return f"""
🚨 POLY SIGNAL ALERT 🚨

📌 {title}

🔴 SELL SIGNAL

💰 YES Price: {yes_price}
📊 Volume: {int(volume):,}
💧 Liquidity: {int(liquidity):,}

⚠️ Market Overheated
📉 Reversal Risk

🎯 Confidence: {confidence}%
"""

    return None
# Aynı marketi tekrar atmamak için
sent_markets = set()

# Ana loop
while True:

    print("Scanning markets...")

    markets = get_markets()  

    print(markets[0])

    for market in markets:

        market_id = market.get("id")

        if market_id in sent_markets:
            continue

        signal = generate_signal(market)

        if signal:
            send(signal)

            print("SIGNAL SENT")

            sent_markets.add(market_id)

    time.sleep(60)