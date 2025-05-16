import discord
import requests
import asyncio
import os

print("📦 Starte Bot...")

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("❌ DISCORD_TOKEN fehlt!")
    exit(1)

SYMBOLS = {
    "BTC": {
        "source": "binance",
        "binance_symbol": "BTCUSDT",
        "channel_id": int(os.getenv("CHANNEL_BTC", 0))
    },
    "GOLD": {
        "source": "binance",
        "binance_symbol": "XAUUSDT",
        "channel_id": int(os.getenv("CHANNEL_GOLD", 0))
    },
    "DAX": {
        "source": "yahoo",
        "yahoo_symbol": "^GDAXI",
        "channel_id": int(os.getenv("CHANNEL_DAX", 0))
    },
    "NASDAQ": {
        "source": "yahoo",
        "yahoo_symbol": "^IXIC",
        "channel_id": int(os.getenv("CHANNEL_NASDAQ", 0))
    },
}

intents = discord.Intents.default()
client = discord.Client(intents=intents)

def get_binance_price(symbol):
    print(f"🔄 Hole Binance-Preis für {symbol}")
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url).json()
    return float(response["price"])

def get_yahoo_price(symbol):
    print(f"🔄 Hole Yahoo-Preis für {symbol}")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m"
    response = requests.get(url).json()
    result = response["chart"]["result"][0]
    return result["meta"]["regularMarketPrice"]

@client.event
async def on_ready():
    print(f"✅ Eingeloggt als {client.user}")
    await update_loop()

async def update_loop():
    await client.wait_until_ready()
    print("🔁 Starte Update-Loop")
    while not client.is_closed():
        for name, config in SYMBOLS.items():
            try:
                channel_id = config["channel_id"]
                if not channel_id:
                    print(f"⚠️ Keine Channel-ID für {name}, überspringe...")
                    continue

                if config["source"] == "binance":
                    price = get_binance_price(config["binance_symbol"])
                elif config["source"] == "yahoo":
                    price = get_yahoo_price(config["yahoo_symbol"])
                else:
                    continue

                channel = client.get_channel(channel_id)
                if channel:
                    formatted = f"{price:,.2f}"
                    new_name = f"📈 {name}: {formatted} $"
                    await channel.edit(name=new_name)
                    print(f"✅ Aktualisiert: {new_name}")
                else:
                    print(f"❌ Channel {channel_id} nicht gefunden")

            except Exception as e:
                print(f"❌ Fehler bei {name}: {e}")

        await asyncio.sleep(30)
