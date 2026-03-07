import discord
from discord.ext import commands
import requests
import os

# Intents aktivieren
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def market(ctx):

    coins = {
        "bitcoin": "BTC",
        "ethereum": "ETH",
        "solana": "SOL",
        "litecoin": "LTC"
    }

    url = "https://api.coingecko.com/api/v3/simple/price"

    params = {
        "ids": ",".join(coins.keys()),
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        embed = discord.Embed(
            title="📊 Crypto Market",
            description="Live Preise",
            color=0x00ff99
        )

        for coin, symbol in coins.items():

            price = data.get(coin, {}).get("usd", "N/A")
            change = data.get(coin, {}).get("usd_24h_change", 0)

            if isinstance(change, float):
                change = round(change, 2)

            arrow = "📈" if change > 0 else "📉"

            embed.add_field(
                name=f"{symbol}",
                value=f"💰 ${price}\n{arrow} 24h: {change}%",
                inline=True
            )

        embed.set_footer(text="Data from CoinGecko")

        await ctx.send(embed=embed)

    except requests.exceptions.RequestException:
        await ctx.send("⚠️ API Fehler – versuche es später erneut.")
    except Exception as e:
        await ctx.send("⚠️ Unerwarteter Fehler.")

# TOKEN aus Environment Variable laden
import os
bot.run(os.getenv("TOKEN"))
