import discord
from discord.ext import commands
import requests
import os
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

coins = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "litecoin": "LTC",
    "solana": "SOL"
}

API_URL = "https://api.coingecko.com/api/v3/simple/price"


def get_prices():
    params = {
        "ids": ",".join(coins.keys()),
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }

    r = requests.get(API_URL, params=params, timeout=10)
    return r.json()


@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user}")


def build_embed(data, title):

    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    embed = discord.Embed(
        title=title,
        description=f"📅 {now}",
        color=0x00ff99
    )

    for coin, symbol in coins.items():

        price = data[coin]["usd"]
        change = round(data[coin]["usd_24h_change"], 2)

        arrow = "📈" if change > 0 else "📉"

        embed.add_field(
            name=symbol,
            value=f"💰 ${price}\n{arrow} 24h: {change}%",
            inline=True
        )

    embed.set_footer(text="Data: CoinGecko")

    return embed


# MARKET
@bot.command()
async def market(ctx):

    try:
        data = get_prices()
        embed = build_embed(data, "📊 Crypto Market")

        await ctx.send(embed=embed)

    except Exception as e:
        print(e)
        await ctx.send("⚠️ Fehler beim Laden der Daten")


# SINGLE PRICE
async def send_price(ctx, coin):

    try:
        data = get_prices()

        price = data[coin]["usd"]
        change = round(data[coin]["usd_24h_change"], 2)

        arrow = "📈" if change > 0 else "📉"

        now = datetime.now().strftime("%d.%m.%Y %H:%M")

        embed = discord.Embed(
            title=f"{coins[coin]} Price",
            description=f"📅 {now}\n\n💰 ${price}\n{arrow} 24h: {change}%",
            color=0x00ff99
        )

        await ctx.send(embed=embed)

    except:
        await ctx.send("⚠️ Preis konnte nicht geladen werden")


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

    sorted_coins = sorted(
        coins.keys(),
        key=lambda x: data[x]["usd_24h_change"],
        reverse=True
    )

    embed = discord.Embed(
        title="📈 Top Gainers",
        color=0x00ff00
    )

    for coin in sorted_coins:

        change = round(data[coin]["usd_24h_change"], 2)
        price = data[coin]["usd"]

        embed.add_field(
            name=coins[coin],
            value=f"${price} | {change}%",
            inline=False
        )

    await ctx.send(embed=embed)


# LOSERS
@bot.command()
async def losers(ctx):

    data = get_prices()

    sorted_coins = sorted(
        coins.keys(),
        key=lambda x: data[x]["usd_24h_change"]
    )

    embed = discord.Embed(
        title="📉 Top Losers",
        color=0xff0000
    )

    for coin in sorted_coins:

        change = round(data[coin]["usd_24h_change"], 2)
        price = data[coin]["usd"]

        embed.add_field(
            name=coins[coin],
            value=f"${price} | {change}%",
            inline=False
        )

    await ctx.send(embed=embed)


bot.run(os.getenv("TOKEN"))
