import discord
from discord.ext import commands, tasks
import requests
import datetime
import os

TOKEN = os.getenv("TOKEN")

coins = ["bitcoin", "ethereum", "solana"]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot ist online als {bot.user}")

@bot.command()
async def market(ctx):
    embed = get_market_embed()
    await ctx.send(embed=embed)

def get_market_embed():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": ",".join(coins), "vs_currencies": "usd"}

    res = requests.get(url, params=params).json()

    embed = discord.Embed(
        title="📊 Market Update",
        description=str(datetime.date.today()),
        color=0x00ff99
    )

    for c in coins:
        price = res[c]["usd"]
        embed.add_field(name=c.upper(), value=f"${price}", inline=True)

    return embed

bot.run(TOKEN)
