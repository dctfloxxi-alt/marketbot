import discord
from discord.ext import commands, tasks
import requests
import os
from datetime import datetime

TOKEN = "DEIN_DISCORD_BOT_TOKEN"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

coins = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "litecoin": "LTC",
    "solana": "SOL"
}

alerts = []
portfolios = {}

API_SIMPLE = "https://api.coingecko.com/api/v3/simple/price"
API_MARKET = "https://api.coingecko.com/api/v3/coins/markets"


def now():
    return datetime.now().strftime("%d.%m.%Y %H:%M")


def get_prices():
    try:

        params = {
            "ids": ",".join(coins.keys()),
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }

        r = requests.get(API_SIMPLE, params=params, timeout=10)

        if r.status_code != 200:
            print("API Error:", r.status_code)
            return None

        return r.json()

    except Exception as e:
        print("Request Error:", e)
        return None


@bot.event
async def on_ready():
    print("Bot online:", bot.user)
    check_alerts.start()


# MARKET
@bot.command()
async def market(ctx):

    data = get_prices()

    if data is None:
        await ctx.send("⚠️ Fehler beim Laden der Daten")
        return

    embed = discord.Embed(
        title="📊 Crypto Market",
        description=f"📅 {now()}",
        color=0x00ff99
    )

    for coin, symbol in coins.items():

        if coin not in data:
            continue

        price = data[coin]["usd"]
        change = round(data[coin]["usd_24h_change"], 2)

        arrow = "📈" if change > 0 else "📉"

        embed.add_field(
            name=symbol,
            value=f"${price}\n{arrow} {change}%",
            inline=True
        )

    await ctx.send(embed=embed)


# SINGLE PRICE
async def send_price(ctx, coin):

    data = get_prices()

    if data is None:
        await ctx.send("⚠️ API Fehler")
        return

    price = data[coin]["usd"]
    change = round(data[coin]["usd_24h_change"], 2)

    arrow = "📈" if change > 0 else "📉"

    embed = discord.Embed(
        title=f"{coins[coin]} Price",
        description=f"📅 {now()}\n\n💰 ${price}\n{arrow} {change}%",
        color=0x00ff99
    )

    await ctx.send(embed=embed)


@bot.command()
async def btc(ctx):
    await send_price(ctx, "bitcoin")


@bot.command()
async def eth(ctx):
    await send_price(ctx, "ethereum")


@bot.command()
async def ltc(ctx):
    await send_price(ctx, "litecoin")


@bot.command()
async def sol(ctx):
    await send_price(ctx, "solana")


# GAINERS
@bot.command()
async def gainers(ctx):

    data = get_prices()

    if data is None:
        await ctx.send("API Fehler")
        return

    sorted_coins = sorted(
        coins.keys(),
        key=lambda x: data[x]["usd_24h_change"],
        reverse=True
    )

    embed = discord.Embed(title="📈 Top Gainers", color=0x00ff00)

    for coin in sorted_coins:

        embed.add_field(
            name=coins[coin],
            value=f"${data[coin]['usd']} | {round(data[coin]['usd_24h_change'],2)}%",
            inline=False
        )

    await ctx.send(embed=embed)


# LOSERS
@bot.command()
async def losers(ctx):

    data = get_prices()

    if data is None:
        await ctx.send("API Fehler")
        return

    sorted_coins = sorted(
        coins.keys(),
        key=lambda x: data[x]["usd_24h_change"]
    )

    embed = discord.Embed(title="📉 Top Losers", color=0xff0000)

    for coin in sorted_coins:

        embed.add_field(
            name=coins[coin],
            value=f"${data[coin]['usd']} | {round(data[coin]['usd_24h_change'],2)}%",
            inline=False
        )

    await ctx.send(embed=embed)


# TOP 10
@bot.command()
async def top(ctx):

    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 10,
        "page": 1
    }

    data = requests.get(API_MARKET, params=params).json()

    embed = discord.Embed(
        title="🏆 Top 10 Cryptos",
        description=f"📅 {now()}",
        color=0xf1c40f
    )

    for coin in data:

        embed.add_field(
            name=coin["symbol"].upper(),
            value=f"${coin['current_price']} | {round(coin['price_change_percentage_24h'],2)}%",
            inline=False
        )

    await ctx.send(embed=embed)


# ALERT
@bot.command()
async def alert(ctx, coin, price: float):

    mapping = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "ltc": "litecoin",
        "sol": "solana"
    }

    coin = mapping.get(coin.lower())

    if coin is None:
        await ctx.send("Coin nicht unterstützt")
        return

    alerts.append({
        "channel": ctx.channel.id,
        "coin": coin,
        "target": price
    })

    await ctx.send(f"🔔 Alert gesetzt für {coin} bei ${price}")


# ALERT CHECK
@tasks.loop(seconds=60)
async def check_alerts():

    if not alerts:
        return

    data = get_prices()

    if data is None:
        return

    for alert in alerts[:]:

        price = data[alert["coin"]]["usd"]

        if price >= alert["target"]:

            channel = bot.get_channel(alert["channel"])

            await channel.send(
                f"🚨 {coins[alert['coin']]} hat ${alert['target']} erreicht!\nAktuell: ${price}"
            )

            alerts.remove(alert)


# PORTFOLIO
@bot.command()
async def portfolio(ctx, action=None, coin=None, amount: float = None):

    user = str(ctx.author.id)

    if user not in portfolios:
        portfolios[user] = {}

    mapping = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "ltc": "litecoin",
        "sol": "solana"
    }

    if action == "add":

        coin = mapping.get(coin)

        if coin is None:
            await ctx.send("Coin nicht unterstützt")
            return

        portfolios[user][coin] = portfolios[user].get(coin, 0) + amount

        await ctx.send("Coin hinzugefügt")

        return

    data = get_prices()

    if data is None:
        await ctx.send("API Fehler")
        return

    total = 0

    embed = discord.Embed(
        title="💼 Portfolio",
        description=f"📅 {now()}",
        color=0x3498db
    )

    for coin, amount in portfolios[user].items():

        price = data[coin]["usd"]
        value = price * amount

        total += value

        embed.add_field(
            name=coins[coin],
            value=f"{amount} → ${round(value,2)}",
            inline=False
        )

    embed.add_field(name="Total", value=f"${round(total,2)}")

    await ctx.send(embed=embed)


bot.run(TOKEN)
