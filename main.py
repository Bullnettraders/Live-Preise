import discord
import requests
import asyncio
import os
import sys

print("📦 Starte Bot...")

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("❌ DISCORD_TOKEN fehlt")
    sys.exit(1)

def check_channel(varname):
    val = os.getenv(varname)
    if not val:
        print(f"❌ {varname} fehlt")
        sys.exit(1)
    try:
        return int(val)
    except ValueError:
        print(f"❌ {varname} ist keine gültige Channel-ID")
        sys.exit(1)

SYMBOLS = {
    "BTC": {
        "source": "binance",
        "binance_symbol": "BTCUSDT",
        "channel_id": check_channel("CHANNEL_BTC")
    },
    "GOLD": {
        "source": "yahoo",
        "yahoo_symbol": "GC=F",
        "channel_id": check_channel("CHANNEL_GOLD")
    },
    "DAX": {
        "source": "yahoo",
        "yahoo_symbol": "^GDAXI",
        "channel_id": check_channel("CHANNEL_DAX")
    },
    "NASDAQ": {
        "source": "yahoo",
        "yahoo_symbol": "^IXIC",
        "channel_id": check_channel("CHANNEL_NASDAQ")
    },
}

intents = discord.Intents.default()
client = discord.Client(intents=intents)

def get_binance_data(symbol):
    print(f"🔄 Binance: {symbol}")
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    res = requests.get(url).json()
    return float(res["lastPrice"]), float(res["priceChangePercent"])

def get_yahoo_data(symbol):
    print(f"🔄 Yahoo: {symbol}")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        raise Exception(f"Yahoo {symbol} fehlgeschlagen")

    data = res.json()
    result = data["chart"]["result"][0]
    meta = result["meta"]
    current = meta["regularMarketPrice"]
    previous = meta.get("chartPreviousClose", current)
    change_percent = ((current - previous) / previous) * 100 if previous else 0.0
    return current, change_percent

@client.event
async def on_ready():
    print(f"✅ Eingeloggt als {client.user}")
    await update_loop()

async def update_loop():
    await client.wait_until_ready()
    print("🔁 Update gestartet")
    last_prices = {}

    while not client.is_closed():
        for name, config in SYMBOLS.items():
            try:
                if config["source"] == "binance":
                    price, change_percent = get_binance_data(config["binance_symbol"])
                else:
                    price, change_percent = get_yahoo_data(config["yahoo_symbol"])

                rounded = round(price, 2)
                last_price = last_prices.get(name)
                last_prices[name] = rounded

                if last_price is not None and abs(rounded - last_price) < 0.10:
                    print(f"⏸ {name}: keine signifikante Änderung ({rounded})")
                    continue

                # Farbkodierter Kreis
                if last_price is not None and rounded > last_price:
                    icon = "🟢"
                elif last_price is not None and rounded < last_price:
                    icon = "🔴"
                else:
                    icon = "⚪"

                percent_str = f"{change_percent:+.2f}%"
                formatted = f"{rounded:,.2f}"
                new_name = f"{icon} {name}: {formatted} $ ({percent_str})"

                channel = client.get_channel(config["channel_id"])
                if channel:
                    print(f"📢 Aktualisiere {name}: {new_name}")
                    await channel.edit(name=new_name)
                else:
                    print(f"❌ Channel für {name} nicht gefunden")

            except Exception as e:
                print(f"❌ Fehler bei {name}: {e}")

        await asyncio.sleep(300)  # 5 Minuten Pause
        

try:
    client.run(TOKEN)
except Exception as e:
    print(f"❌ Discord-Login fehlgeschlagen: {e}")
