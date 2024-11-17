import os
import sys
from dotenv import load_dotenv
import discord
from discord.ext import commands
from transformers import pipeline


pipe = pipeline(
    "text-generation",
    model="meta-llama/Llama-3.2-1B-Instruct"
)

SYSTEM_PROMPT = """
    You are a discord bot meant to give laptop recommendations based
    on user input. You will ask for information about the user's needs
    and use cases as necessary to give the best recommendation possible.
    """


def make_response(text):
    message_structure = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text}
    ]

    response_obj = pipe(
        message_structure,
        max_new_tokens=500
    )

    response = response_obj[0]["generated_text"][-1]["content"]
    return response


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
async def ping(ctx):
    await ctx.send("pong")


@bot.command()
async def restart(_ctx):
    os.execl(sys.executable, sys.executable, *sys.argv)


@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if (message.content.startswith('~')):
        try:
            await message.channel.send(make_response(message.content), reference=message)
        except Exception as e:
            await message.channel.send(str(e), reference=message)


bot.run(token)
