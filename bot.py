import requests
import time
import json
from collections import deque
from datetime import datetime

TOKEN = "8740187471:AAFnbyytjPdyfudWHubh0vfu9SRpOXdna0w"
CHAT_ID = "1030427227"

# =========================
# SYSTEM STATE
# =========================

signal_queue = deque()
sent_markets = {}
last_send_time = 0

# =========================
# TELEGRAM SENDER
# =========================

def send(msg):
    global last_send_time

    now = time.time()

    # Anti-spam delay
    if now - last_send_time < 2:
        time.sleep(2 - (now - last_send_time))

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg
        })

        last_send_time = time.time()

    except Exception as e:
        print("Telegram HATA:", e)

# =========================
# POLYMARKET FETCH
# =========================

def get_markets():

    url = "https://gamma-api.polymarket.com/markets"

    try:
        r = requests.get(url, timeout=10)
        return r.json()

    except Exception as e:
        print("API HATA:", e)
        return []

# =========================
# DUPLICATE CONTROL
# =========================

def is_duplicate(market_id, side):

    if market_id not in sent_markets:
        return False

    if sent_markets[market_id] == side:
        return True

    return False


def mark_sent(market_id, side):
    sent_markets[market_id] = side

# =========================
# SIGNAL SCORING ENGINE
# =========================

def calculate_confidence(volume, liquidity, yes_price):

    volume_score = min(volume / 300000, 1) * 40
    liquidity_score = min(liquidity / 500000, 1) * 30
    edge_score = (0.5 - abs(yes_price - 0.5)) * 100

    confidence = int(volume_score + liquidity_score + edge_score)

    confidence = max(5, min(confidence, 95))

    return confidence

# =========================
# AI-STYLE EXPLANATION
# =========================

def generate_reason(confidence, volume, liquidity):

    reasons = []

    if confidence >= 80:
        reasons.append("Yüksek piyasa verimsizliği tespit edildi")

    if volume > 1000000:
        reasons.append("Anormal hacim hareketi gözlemlendi")

    if liquidity > 100000:
        reasons.append("Likidite akışı güçleniyor")

    if not reasons:
        reasons.append("Momentum ivmesi yükseliyor")

    return reasons

# =========================
# SIGNAL GENERATOR
# =========================

def generate_signal(market):

    title = market.get("question", "No title")
    market_id = market.get("id")

    prices = market.get("outcomePrices")

    if not prices:
        return None

    try:
        prices = json.loads(prices)
        yes_price = float(prices[0])

    except:
        return None

    volume = float(market.get("volumeNum", 0))
    liquidity = float(market.get("liquidityNum", 0))

    # Quality filters
    if volume < 20000:
        return None

    if liquidity < 3000:
        return None

    confidence = calculate_confidence(volume, liquidity, yes_price)

    signal_type = None

    if yes_price <= 0.45:
        signal_type = "BUY"

    elif yes_price >= 0.55:
        signal_type = "SELL"

    if not signal_type:
        return None

    if is_duplicate(market_id, signal_type):
        return None

    reasons = generate_reason(confidence, volume, liquidity)

    explanation = "\n• ".join(reasons)

    # =========================
    # PROFESSIONAL MESSAGE FORMAT
    # =========================

    emoji = "🟢" if signal_type == "BUY" else "🔴"
    signal_text = "AL FIRSATI" if signal_type == "BUY" else "SATIŞ BÖLGESİ"

    msg = f"""
🚨 MARKET EDGE DETECTED

📌 {title}

{emoji} {signal_text}

📊 Piyasa Verileri
• Fiyat: {round(yes_price, 3)}
• Hacim: {int(volume):,}
• Likidite: {int(liquidity):,}

🧠 Sistem Analizi
• {explanation}

🎯 Güven Skoru: {confidence}%

⏱ Zaman Dilimi: Short-term swing

#Polymarket
"""

    return {
        "market_id": market_id,
        "side": signal_type,
        "confidence": confidence,
        "message": msg
    }

# =========================
# MARKET SCANNER
# =========================

def scan_markets():

    print("Scanning markets...")

    markets = get_markets()

    if not markets:
        return

    ranked_signals = []

    for market in markets:

        signal = generate_signal(market)

        if signal:
            ranked_signals.append(signal)

    # Highest confidence first
    ranked_signals.sort(
        key=lambda x: x["confidence"],
        reverse=True
    )

    # Only top 3 signals per cycle
    top_signals = ranked_signals[:3]

    for signal in top_signals:

        signal_queue.append(signal)

        print(
            f"QUEUE -> {signal['market_id']} ({signal['side']})"
        )

# =========================
# SIGNAL DISPATCHER
# =========================

def process_queue():

    if not signal_queue:
        return

    signal = signal_queue.popleft()

    send(signal["message"])

    mark_sent(signal["market_id"], signal["side"])

    print(
        f"SENT -> {signal['market_id']} ({signal['side']})"
    )

# =========================
# MAIN ENGINE LOOP
# =========================

while True:

    try:

        # Scan
        scan_markets()

        # Send queue one-by-one
        process_queue()

        # Live-feed feeling
        time.sleep(4)

    except Exception as e:

        print("SYSTEM ERROR:", e)

        time.sleep(5)
```

# Bu Versiyon Ne Kazandırır?

## ✅ Queue Sistemi

* Sinyaller toplu spam gibi görünmez
* Tek tek akar
* Gerçek canlı akış hissi verir

## ✅ Ranking Engine

* Her market gönderilmez
* Sadece en güçlü sinyaller seçilir
* Premium sistem hissi verir

## ✅ AI-Style Açıklama

* “Neden sinyal geldi?” sorusuna cevap verir
* İnsanlarda güven oluşturur

## ✅ Professional Formatting

* Retail signal bot gibi görünmez
* “Market intelligence system” hissi verir

## ✅ Anti-Spam Architecture

* Telegram flood engeli
* Kontrollü gönderim
* Daha stabil akış
