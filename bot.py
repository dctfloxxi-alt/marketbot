import discord
from discord.ext import commands
import requests
import os

# Discord intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Coins
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


# MARKET OVERVIEW
@bot.command()
async def market(ctx):

    try:
        data = get_prices()

        embed = discord.Embed(
            title="📊 Crypto Market",
            description="Live Preise",
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

        await ctx.send(embed=embed)

    except:
        await ctx.send("⚠️ Fehler beim Laden der Daten")


# SINGLE PRICE COMMAND
async def send_price(ctx, coin):

    try:
        data = get_prices()

        price = data[coin]["usd"]
        change = round(data[coin]["usd_24h_change"], 2)

        arrow = "📈" if change > 0 else "📉"

        embed = discord.Embed(
            title=f"{coins[coin]} Price",
            description=f"💰 ${price}\n{arrow} 24h: {change}%",
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


bot.run(os.getenv("TOKEN"))
