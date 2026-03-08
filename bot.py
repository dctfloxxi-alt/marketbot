from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()
import discord
from discord.ext import commands, tasks
from discord import app_commands
import requests
import asyncio
from datetime import datetime
import json
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===============================
# CONFIG
# ===============================

API_SIMPLE = "https://api.coingecko.com/api/v3/simple/price"
API_MARKET = "https://api.coingecko.com/api/v3/coins/markets"

coins = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "litecoin": "LTC",
    "solana": "SOL",
    "ripple": "XRP",
    "cardano": "ADA"
}

alerts = []
portfolios = {}
chart_channel = None

# ===============================
# UTILS
# ===============================

def now():
    return datetime.now().strftime("%d.%m.%Y %H:%M")

def get_prices():
    params = {
        "ids": ",".join(coins.keys()),
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    try:
        r = requests.get(API_SIMPLE, params=params, timeout=10)
        return r.json()
    except:
        return None


def get_market():
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 10,
        "page": 1
    }
    try:
        r = requests.get(API_MARKET, params=params, timeout=10)
        return r.json()
    except:
        return None


# ===============================
# BOT READY
# ===============================

@bot.event
async def on_ready():
    print("================================")
    print("BOT ONLINE")
    print(bot.user)
    print("================================")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

    check_alerts.start()
    live_charts.start()
   


# ===============================
# MARKET
# ===============================

@bot.tree.command(name="market", description="Crypto Markt")
async def market(interaction: discord.Interaction):

    data = get_prices()
    if not data:
        await interaction.response.send_message("⚠️ API Fehler")
        return

    embed = discord.Embed(
        title="📊 Crypto Market",
        description=f"📅 {now()}",
        color=0x00ff99
    )

    for coin, symbol in coins.items():
        coin_data = data.get(coin)
        if not coin_data:
            continue

        price = coin_data.get("usd", 0)
        change = coin_data.get("usd_24h_change", 0)
        arrow = "📈" if change >= 0 else "📉"

        embed.add_field(
            name=symbol,
            value=f"${price}\n{arrow} {round(change,2)}%",
            inline=True
        )

    await interaction.response.send_message(embed=embed)

# ===============================
# SINGLE PRICE
# ===============================

async def coin_price(interaction, coin):

    data = get_prices()

    if not data:
        await interaction.response.send_message("⚠️ API Fehler")
        return

    coin_data = data.get(coin)

    if not coin_data:
        await interaction.response.send_message("Coin nicht gefunden")
        return

    price = coin_data.get("usd", 0)
    change = coin_data.get("usd_24h_change", 0)

    arrow = "📈" if change >= 0 else "📉"

    embed = discord.Embed(
        title=f"{coins[coin]} Preis",
        description=f"${price}\n{arrow} {round(change,2)}%",
        color=0x00ff00
    )

    await interaction.response.send_message(embed=embed)
    
@bot.tree.command()
async def btc(interaction: discord.Interaction):
    await coin_price(interaction, "bitcoin")

@bot.tree.command()
async def eth(interaction: discord.Interaction):
    await coin_price(interaction, "ethereum")

@bot.tree.command()
async def sol(interaction: discord.Interaction):
    await coin_price(interaction, "solana")

# ===============================
# TOP 10
# ===============================
@bot.tree.command()
async def top(interaction: discord.Interaction):

    data = get_market()
    if not data:
        await interaction.response.send_message("API Fehler")
        return

    embed = discord.Embed(
        title="🏆 Top 10 Cryptos",
        color=0xf1c40f
    )

    for coin in data:
        embed.add_field(
            name=coin["symbol"].upper(),
            value=f"${coin['current_price']} | {round(coin['price_change_percentage_24h'],2)}%",
            inline=False
        )

    await interaction.response.send_message(embed=embed)
# ===============================
# GAINERS / LOSERS
# ===============================

@bot.tree.command()
async def gainers(interaction: discord.Interaction):
    data = get_market()

    data = sorted(
        data,
        key=lambda x: x["price_change_percentage_24h"],
        reverse=True
    )

    embed = discord.Embed(title="📈 Top Gainers", color=0x00ff00)

    for coin in data[:5]:
        embed.add_field(
            name=coin["symbol"].upper(),
            value=f"{coin['price_change_percentage_24h']:.2f}%",
            inline=False
        )

    await interaction.response.send_message(embed=embed)
@bot.tree.command()
async def losers(interaction: discord.Interaction):

    data = get_market()

    data = sorted(
        data,
        key=lambda x: x["price_change_percentage_24h"]
    )

    embed = discord.Embed(title="📉 Top Losers", color=0xff0000)

    for coin in data[:5]:

        embed.add_field(
            name=coin["symbol"].upper(),
            value=f"{coin['price_change_percentage_24h']:.2f}%",
            inline=False
        )

    await interaction.response.send_message(embed=embed)


# ===============================
# ALERT SYSTEM
# ===============================

@bot.tree.command()
async def alert(interaction: discord.Interaction, coin: str, price: float):

    mapping = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "sol": "solana"
    }

    coin = mapping.get(coin.lower())

    if not coin:
        await interaction.response.send_message("Coin nicht unterstützt")
        return

    alerts.append({
        "channel": interaction.channel.id,
        "coin": coin,
        "price": price
    })

    await interaction.response.send_message(f"🚨 Alert gesetzt bei ${price}")
    
@tasks.loop(seconds=60)
async def check_alerts():

    if not alerts:
        return

    data = get_prices()

    for alert in alerts[:]:

        coin = alert["coin"]

        if coin not in data:
            continue

        price = data[coin]["usd"]

        if price >= alert["price"]:

            channel = bot.get_channel(alert["channel"])

            await channel.send(
                f"🚨 ALERT\n{coins[coin]} hat ${alert['price']} erreicht!\nAktuell: ${price}"
            )

            alerts.remove(alert)

@tasks.loop(minutes=5)
async def live_charts():

    if chart_channel is None:
        return

    data = get_prices()

    if not data:
        return

    embed = discord.Embed(
        title="📊 Live Crypto Market",
        description=f"📅 {now()}",
        color=0x00ff99
    )

    for coin, symbol in coins.items():

        coin_data = data.get(coin)

        if not coin_data:
            continue

        price = coin_data["usd"]
        change = coin_data["usd_24h_change"]

        arrow = "📈" if change >= 0 else "📉"

        embed.add_field(
            name=symbol,
            value=f"${price}\n{arrow} {round(change,2)}%",
            inline=True
        )

    await chart_channel.send(embed=embed)

# ===============================
# PORTFOLIO
# ===============================

@bot.tree.command()
async def portfolio(interaction: discord.Interaction, action: str=None, coin: str=None, amount: float=None):

    user = str(interaction.user.id)

    mapping = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "sol": "solana"
    }

    if user not in portfolios:
        portfolios[user] = {}

    if action == "add":
        coin = mapping.get(coin)

        if not coin:
            await interaction.response.send_message("Coin nicht unterstützt")
            return

        portfolios[user][coin] = portfolios[user].get(coin, 0) + amount

        await interaction.response.send_message("✅ Coin hinzugefügt")
        return

    data = get_prices()
    total = 0

    embed = discord.Embed(title="💼 Portfolio", color=0x3498db)

    for coin, amount in portfolios[user].items():
        price = data[coin]["usd"]
        value = price * amount
        total += value

        embed.add_field(
            name=coins[coin],
            value=f"{amount} → ${round(value,2)}",
            inline=False
        )

    embed.add_field(
        name="Total",
        value=f"${round(total,2)}"
    )

    await interaction.response.send_message(embed=embed)
    
@bot.tree.command(name="setchannel", description="Setzt Live Chart Channel")
async def setchannel(interaction: discord.Interaction):

    global chart_channel
    chart_channel = interaction.channel

    await interaction.response.send_message(
        f"✅ Live Chart Channel gesetzt auf {interaction.channel.mention}"
    )
    
# ===============================
# HELP COMMAND
# ===============================

@bot.tree.command()
async def cryptohelp(interaction: discord.Interaction):

    embed = discord.Embed(
        title="Crypto Bot Commands",
        color=0x7289da
    )

    embed.add_field(name="Market", value="!market", inline=False)
    embed.add_field(name="Coin Preise", value="!btc !eth !sol", inline=False)
    embed.add_field(name="Top Coins", value="!top", inline=False)
    embed.add_field(name="Gainers / Losers", value="!gainers !losers", inline=False)
    embed.add_field(name="Portfolio", value="!portfolio add btc 0.5", inline=False)
    embed.add_field(name="Alerts", value="!alert btc 70000", inline=False)

    await interaction.response.send_message(embed=embed)

# ===============================
# START
# ===============================

keep_alive()
bot.run(TOKEN)
