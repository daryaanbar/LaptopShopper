import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from transformers import pipeline
import torch


MODEL_PATH = '/home/andrewsenth/llama_model_hf'

pipe = pipeline(
    "text-generation",
    model=MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map="auto"
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


@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if (message.content.startswith('~')):
        await message.channel.send(make_response(message.content), reference=message)


bot.run(token)
