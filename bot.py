import requests
import time
import json
from collections import deque

TOKEN = "8740187471:AAFnbyytjPdyfudWHubh0vfu9SRpOXdna0w"
CHAT_ID = "1030427227"

signal_queue = deque()
sent_signals = {}
COOLDOWN = 3600  # 1 hour

last_send_time = 0


# =========================
# TELEGRAM SEND
# =========================
def send(msg):
    global last_send_time

    now = time.time()

    # Telegram rate limit protection
    if now - last_send_time < 1.5:
        time.sleep(1.5 - (now - last_send_time))

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg
        })
        last_send_time = time.time()

    except Exception as e:
        print("Telegram error:", e)


# =========================
# FETCH MARKETS
# =========================
def get_markets():
    try:
        r = requests.get("https://gamma-api.polymarket.com/markets", timeout=10)
        return r.json()
    except:
        return []


# =========================
# COOLDOWN CHECK
# =========================
def is_duplicate(market_id, side):
    key = f"{market_id}_{side}"

    if key not in sent_signals:
        return False

    if time.time() - sent_signals[key] < COOLDOWN:
        return True

    return False


def mark_sent(market_id, side):
    key = f"{market_id}_{side}"
    sent_signals[key] = time.time()


# =========================
# SIGNAL ENGINE
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

    # filters
    if volume < 20000 or liquidity < 3000:
        return None

    side = None

    if yes_price <= 0.45:
        side = "BUY"
    elif yes_price >= 0.55:
        side = "SELL"
    else:
        return None

    if is_duplicate(market_id, side):
        return None

    msg = f"""
🚨 MARKET SIGNAL

📌 {title}

📊 Price: {round(yes_price, 3)}
📊 Volume: {int(volume):,}
📊 Liquidity: {int(liquidity):,}

🧠 Signal: {side}

#Polymarket
"""

    return market_id, side, msg


# =========================
# SCANNER
# =========================
def scan():

    print("Scanning markets...")

    markets = get_markets()

    for m in markets:

        result = generate_signal(m)

        if result:
            market_id, side, msg = result
            signal_queue.append((market_id, side, msg))


# =========================
# SENDER
# =========================
def process_queue():

    if not signal_queue:
        return

    market_id, side, msg = signal_queue.popleft()

    send(msg)

    mark_sent(market_id, side)

    print("SENT:", market_id, side)


# =========================
# MAIN LOOP
# =========================
while True:

    try:
        scan()
        process_queue()
        time.sleep(3)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)
