import os
import sys
import time
import threading
from dataclasses import dataclass
from dotenv import load_dotenv
import schedule
import discord
from discord.ext import commands
from transformers import pipeline
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss


# init LLM

pipe = pipeline(
    "text-generation",
    model="meta-llama/Llama-3.2-1B-Instruct",
    device=0
)

SYSTEM_PROMPT = """
    You are a discord bot named LaptopPal meant to give laptop recommendations based
    on user input. You will ask for information about the user's needs
    and use cases as necessary to give the best recommendation possible.
    Assume a user has just invoked you and is expecting an initial response
    to get them started. Assume nothing about the user's requirements at first.
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


# load knowledge base

def load_and_split(file_paths, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = []
    for file_path in file_paths:
        with open(file_path, 'r') as f:
            text = f.read()
        docs.extend(splitter.split_text(text))
    return docs


def embed_chunks(chunks, embedding_model='all-MiniLM-L6-v2'):
    model = SentenceTransformer(embedding_model)
    embeddings = model.encode(chunks)
    return np.array(embeddings)


def build_index(embeddings):
    index = faiss.IndexFlatL2(embeddings.shape[1])  # L2 distance
    index.add(embeddings)
    return index

kb_directory = 'kb'

kb_file_paths = [
    os.path.join(kb_directory, file) for file in os.listdir(kb_directory)
    if os.path.isfile(os.path.join(kb_directory, file))
]

kb_chunks = load_and_split(kb_file_paths)
kb_embeddings = embed_chunks(kb_chunks)
kb_index = build_index(kb_embeddings)


# message generation

def retrieve(query, embedding_model='all-MiniLM-L6-v2', top_k=5):
    model = SentenceTransformer(embedding_model)
    query_embedding = model.encode([query])
    distances, indices = kb_index.search(query_embedding, top_k)
    return [kb_chunks[i] for i in indices[0]]


def augment_prompt(query, retrieved_docs):
    context = "\n".join(retrieved_docs)
    return f"Context:\n{context}\n\nQuery: {query}\nAnswer:"


def make_response(text: str, user_id: str) -> str:
    retrieved_docs = retrieve(text)
    prompt = augment_prompt(text, retrieved_docs)

    message_structure = user_mem[user_id].chat_history
    message_structure.append({"role": "user", "content": prompt})

    response_obj = pipe(
        message_structure,
        max_new_tokens=500
    )

    response = response_obj[0]["generated_text"][-1]["content"]
    message_structure.append({"role": "assistant", "content": response})
    user_mem[user_id].chat_history = message_structure
    user_mem[user_id].last_updated = time.time()

    return response


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
