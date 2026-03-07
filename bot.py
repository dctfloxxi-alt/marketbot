import discord
from discord.ext import commands
import requests

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def market(ctx):

    coins = ["bitcoin", "ethereum", "solana", "litecoin"]

    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(coins),
        "vs_currencies": "usd"
    }

    try:
        r = requests.get(url, params=params)
        data = r.json()

        embed = discord.Embed(
            title="📊 Crypto Market Prices",
            color=0x00ff99
        )

        for coin in coins:
            price = data.get(coin, {}).get("usd", "N/A")
            embed.add_field(
                name=coin.upper(),
                value=f"${price}",
                inline=True
            )

        embed.set_footer(text="Data from CoinGecko")

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send("⚠️ Fehler beim Laden der Preise.")

bot.run("DEIN_TOKEN")
