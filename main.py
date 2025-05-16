import discord
import requests
import asyncio
import os
import sys

print("📦 Starte Bot...")

# ENV prüfen
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("❌ Umgebungsvariable DISCORD_TOKEN fehlt!")
    sys.exit(1)

def check_channel(varname):
    val = os.getenv(varname)
    if not val:
        print(f"❌ Umgebungsvariable {varname} fehlt!")
        sys.exit(1)
    try:
        return int(val)
    except ValueError:
        print(f"❌ Umgebungsvariable {varname} ist keine gültige Channel-ID!")
        sys.exit(1)

SYMBOLS = {
    "BTC": {
        "source": "binance",
        "binance_symbol": "BTCUSDT",
        "channel_id": check_channel("CHANNEL_BTC")
    },
    "GOLD": {
        "source": "yahoo",
        "yahoo_symbol": "XAUUSD=X",
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

def get_binance_price(symbol):
    print(f"🔄 Hole Binance-Preis für {symbol}")
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url).json()
    if "price" not in response:
        raise Exception(f"Keine Preis-Daten für {symbol}")
    return float(response["price"])

def get_yahoo_price(symbol):
    print(f"🔄 Hole Yahoo-Preis für {symbol}")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code} – {response.text[:100]}")

    data = response.json()
    result = data["chart"]["result"][0]
    return result["meta"]["regularMarketPrice"]

@client.event
async def on_ready():
    print(f"✅ Eingeloggt als {client.user}")
    await update_loop()

async def update_loop():
    await client.wait_until_ready()
    print("🔁 Starte Update-Loop")

    last_prices = {}

    while not client.is_closed():
        for name, config in SYMBOLS.items():
            try:
                price = (
                    get_binance_price(config["binance_symbol"])
                    if config["source"] == "binance"
                    else get_yahoo_price(config["yahoo_symbol"])
                )

                rounded = round(price, 2)
                last_price = last_prices.get(name)

                # Preisvergleich mit Toleranz
                if last_price is not None and abs(rounded - last_price) < 0.10:
                    print(f"⏸ {name}: Änderung ({rounded}) < 0.10 → kein Update.")
                    continue

                last_prices[name] = rounded
                formatted = f"{rounded:,.2f}"
                new_name = f"📈 {name}: {formatted} $"
                channel = client.get_channel(config["channel_id"])

                if channel:
                    await channel.edit(name=new_name)
                    print(f"✅ Aktualisiert: {new_name}")
                else:
                    print(f"❌ Channel {config['channel_id']} nicht gefunden")

            except Exception as e:
                print(f"❌ Fehler bei {name}: {e}")

        await asyncio.sleep(30)

try:
    client.run(TOKEN)
except Exception as e:
    print(f"❌ Discord-Login fehlgeschlagen: {e}")
