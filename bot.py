import requests
import time
import json
from datetime import datetime

TOKEN = "8740187471:AAFnbyytjPdyfudWHubh0vfu9SRpOXdna0w"
CHAT_ID = "1030427227"

sent_signals = {}
last_send_time = 0

# aynı market aynı yönü tekrar atmasın
COOLDOWN = 3600  # 1 saat


def send(msg):
    global last_send_time

    # Telegram spam koruması
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


# =========================
# DUPLICATE + COOLDOWN
# =========================
def is_duplicate(fingerprint):

    if fingerprint not in sent_signals:
        return False

    last_sent = sent_signals[fingerprint]

    # cooldown kontrolü
    if time.time() - last_sent < COOLDOWN:
        return True

    return False


def mark_sent(fingerprint):

    sent_signals[fingerprint] = time.time()


# =========================
# SIGNAL ENGINE
# =========================
def generate_signal(market):

    title = market.get("question", "No title")
    market_id = market.get("id")

    prices = market.get("outcomePrices")

    if not prices:
        return None, None, None

    try:
        prices = json.loads(prices)
        yes_price = float(prices[0])

    except:
        return None, None, None

    volume = float(market.get("volumeNum", 0))
    liquidity = float(market.get("liquidityNum", 0))

    # 🔥 filtreler gevşetildi
    if volume < 5000:
        return None, None, None

    if liquidity < 1000:
        return None, None, None

    volume_score = min(volume / 200000, 1) * 40
    liquidity_score = min(liquidity / 500000, 1) * 30
    edge_score = (0.5 - abs(yes_price - 0.5)) * 100

    confidence = int(volume_score + liquidity_score + edge_score)

    confidence = max(5, min(confidence, 95))

    side = None

    # 🔥 daha fazla fırsat yakalar
    if yes_price <= 0.48:
        side = "BUY"

    elif yes_price >= 0.52:
        side = "SELL"

    else:
        return None, None, None

    # 🔥 gerçek duplicate kontrol
    fingerprint = f"{market_id}_{side}_{round(yes_price, 2)}"

    if is_duplicate(fingerprint):
        return None, None, None

    # =========================
    # BUY
    # =========================
    if side == "BUY":

        msg = f"""
🚨 POLY SİNYAL UYARISI 🚨

📌 {title}

🟢 AL SİNYALİ

💰 Giriş Bölgesi: {round(yes_price, 2)} - {round(yes_price + 0.03, 2)}

🎯 Güven Skoru: {confidence}%

📊 Hacim: {int(volume):,}
💧 Likidite: {int(liquidity):,}

⚡ Momentum güçleniyor
📈 Market baskısı artıyor

#Polymarket
"""

    # =========================
    # SELL
    # =========================
    else:

        msg = f"""
🚨 POLY SİNYAL UYARISI 🚨

📌 {title}

🔴 SAT SİNYALİ

💰 Çıkış Bölgesi: {round(yes_price, 2)} - {round(yes_price - 0.03, 2)}

🎯 Güven Skoru: {confidence}%

📊 Hacim: {int(volume):,}
💧 Likidite: {int(liquidity):,}

⚠️ Market aşırı ısındı
📉 Geri çekilme riski yükseliyor

#Polymarket
"""

    return msg, side, fingerprint


# =========================
# MAIN LOOP
# =========================
while True:

    print("Scanning markets...")

    markets = get_markets()

    if not markets:
        time.sleep(5)
        continue

    for market in markets:

        signal, side, fingerprint = generate_signal(market)

        if signal:

            print("SIGNAL FOUND")

            # ⚡ anında gönder
            send(signal)

            print(f"SİNYAL GÖNDERİLDİ -> {fingerprint}")

            mark_sent(fingerprint)

            # burst engel
            time.sleep(1.5)

    # live feed hissi
    time.sleep(5)
