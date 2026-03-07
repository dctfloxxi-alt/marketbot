import discord
from discord.ext import tasks
import requests
import datetime
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

coins = ["bitcoin", "ethereum", "solana"]

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print("Bot ist online!")
    post_update.start()

@tasks.loop(hours=24)
async def post_update():
    channel = client.get_channel(CHANNEL_ID)
    embed = get_market_embed()
    await channel.send(embed=embed)

def get_market_embed():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": ",".join(coins), "vs_currencies": "usd"}
    res = requests.get(url, params=params).json()

    embed = discord.Embed(
        title="📊 Daily Market Update",
        description=str(datetime.date.today()),
        color=0x00ff99
    )

    for c in coins:
        price = res[c]["usd"]
        embed.add_field(name=c.upper(), value=f"${price}", inline=True)

    return embed

client.run(TOKEN)
