import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

#bump


intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    intents=intents,
    command_prefix='!',
    description='A simple Discord bot')

load_dotenv()
token = os.getenv('BOT_TOKEN')


@bot.command()
async def hello(ctx):
    await ctx.send("Hello!")


bot.run(token)
