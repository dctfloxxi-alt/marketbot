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

    await bot.tree.sync()   # WICHTIG für Slash Commands

    check_alerts.start()
    live_charts.start()
   


# ===============================
# MARKET
# ===============================

@bot.tree.command()
async def market(ctx):

    data = get_prices()

    if not data:
        await ctx.send("⚠️ API Fehler")
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

    await ctx.send(embed=embed)


# ===============================
# SINGLE PRICE
# ===============================

async def coin_price(ctx, coin):

    data = get_prices()

    if not data:
        await ctx.send("⚠️ API Fehler")
        return

    coin_data = data.get(coin)

    if not coin_data:
        await ctx.send("Coin nicht gefunden")
        return

    price = coin_data.get("usd", 0)
    change = coin_data.get("usd_24h_change", 0)

    arrow = "📈" if change >= 0 else "📉"

    embed = discord.Embed(
        title=f"{coins[coin]} Preis",
        description=f"${price}\n{arrow} {round(change,2)}%",
        color=0x00ff00
    )

    await ctx.send(embed=embed)


@bot.tree.command()
async def btc(ctx):
    await coin_price(ctx, "bitcoin")


@bot.tree.command()
async def eth(ctx):
    await coin_price(ctx, "ethereum")


@bot.tree.command()
async def sol(ctx):
    await coin_price(ctx, "solana")


# ===============================
# TOP 10
# ===============================

@bot.tree.command()
async def top(ctx):

    data = get_market()

    if not data:
        await ctx.send("API Fehler")
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

    await ctx.send(embed=embed)


# ===============================
# GAINERS / LOSERS
# ===============================

@bot.tree.command()
async def gainers(ctx):

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

    await ctx.send(embed=embed)

@bot.tree.command()
async def losers(ctx):

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

    await ctx.send(embed=embed)


# ===============================
# ALERT SYSTEM
# ===============================
@bot.tree.command()
async def alert(ctx, coin, price: float):

    mapping = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "sol": "solana"
    }

    coin = mapping.get(coin.lower())

    if not coin:
        await ctx.send("Coin nicht unterstützt")
        return

    alerts.append({
        "channel": ctx.channel.id,
        "coin": coin,
        "price": price
    })

    await ctx.send(f"🚨 Alert gesetzt bei ${price}")


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
async def portfolio(ctx, action=None, coin=None, amount: float = None):

    user = str(ctx.author.id)

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
            await ctx.send("Coin nicht unterstützt")
            return

        portfolios[user][coin] = portfolios[user].get(coin, 0) + amount

        await ctx.send("Coin hinzugefügt")
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

    await ctx.send(embed=embed)
   
    @bot.tree.command()
async def setchannel(ctx):
    global chart_channel
    chart_channel = ctx.channel
    await ctx.send(f"✅ Live Chart Channel gesetzt auf {ctx.channel.mention}")

# ===============================
# HELP COMMAND
# ===============================

@bot.tree.command()
async def cryptohelp(ctx):

    embed = discord.Embed(
        title="Crypto Bot Commands",
        color=0x7289da
    )

    embed.add_field(
        name="Market",
        value="!market",
        inline=False
    )

    embed.add_field(
        name="Coin Preise",
        value="!btc !eth !sol",
        inline=False
    )

    embed.add_field(
        name="Top Coins",
        value="!top",
        inline=False
    )

    embed.add_field(
        name="Gainers / Losers",
        value="!gainers !losers",
        inline=False
    )

    embed.add_field(
        name="Portfolio",
        value="!portfolio add btc 0.5",
        inline=False
    )

    embed.add_field(
        name="Alerts",
        value="!alert btc 70000",
        inline=False
    )

    await ctx.send(embed=embed)


# ===============================
# START
# ===============================

keep_alive()
bot.run(TOKEN)
