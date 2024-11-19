import os
import sys
import time
import threading
from dataclasses import dataclass
from dotenv import load_dotenv
import discord
from discord.ext import commands
from transformers import pipeline
import schedule


# init LLM

pipe = pipeline(
    "text-generation",
    model="meta-llama/Llama-3.2-1B-Instruct"
)

SYSTEM_PROMPT = """
    You are a discord bot meant to give laptop recommendations based
    on user input. You will ask for information about the user's needs
    and use cases as necessary to give the best recommendation possible.
    Assume a user has just invoked you and is expecting an initial response
    to get them started.
    """


# init system memory

@dataclass
class UserData:
    user_id: str
    channel_name: str
    last_updated: float
    chat_history: list

user_mem: dict[str, UserData] = {}


# periodically clear memory

MAX_TIMEOUT = 600 #seconds

def bg_task():
    now = time.time()
    user_mem = {
        k: v for (k, v) in user_mem.entries()
        if now - v.last_updated < MAX_TIMEOUT
    }

schedule.every(10).minutes.do(bg_task)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

schedule_thread = threading.Thread(target=run_schedule)
schedule_thread.daemon = True
schedule_thread.start()


# bot logic

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

COMMAND_PREFIX = '!'

bot = commands.Bot(
    intents=intents,
    command_prefix=COMMAND_PREFIX,
    description='A simple Discord bot')

load_dotenv()
token = os.getenv('BOT_TOKEN')


@bot.command()
async def ping(ctx):
    await ctx.send("pong")


@bot.command()
async def restart(ctx):
    try:
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        await ctx.send(str(e))


def make_response(text: str, user_id: str) -> str:
    message_structure = user_mem[user_id].chat_history
    message_structure.append({"role": "user", "content": text})

    response_obj = pipe(
        message_structure,
        max_new_tokens=500
    )

    response = response_obj[0]["generated_text"][-1]["content"]
    message_structure.append({"role": "assistant", "content": response})
    user_mem[user_id].chat_history = message_structure
    user_mem[user_id].last_updated = time.time()

    return response


@bot.command()
async def shop(ctx):
    try:
        user_id = ctx.author.id
        channel_name = ctx.channel.name
        message_structure = [{"role": "system", "content": SYSTEM_PROMPT}]
        user_mem[user_id] = UserData(user_id, channel_name, time.time(), message_structure)

        await ctx.send(make_response("", user_id))
    except Exception as e:
        await ctx.send(str(e))


@bot.event
async def on_message(message):
    try:
        await bot.process_commands(message)

        msg_content = message.content
        user_id = message.author.id
        channel_name = message.channel.name

        if (
            msg_content.startswith(COMMAND_PREFIX) or
            user_id == bot.user.id or
            user_id not in user_mem or
            user_mem[user_id].channel_name != channel_name
        ):
            return

        await message.channel.send(make_response(msg_content, user_id), reference=message)
    except Exception as e:
        await message.channel.send(str(e), reference=message)


bot.run(token)
