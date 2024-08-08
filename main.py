import asyncio
import dotenv
import os

import discord
from discord.ext import commands

dotenv.load_dotenv(dotenv.find_dotenv())


client = commands.Bot(
    description="Discord Bot", command_prefix="!", intents=discord.Intents.all())

@client.event
async def on_ready():
    print("Main 出發!")
    print("-----------------------------")


async def main():

    Token = os.getenv("TOKEN",'')
    
    await client.load_extension("cog")
    await client.start(Token)




asyncio.run(main())