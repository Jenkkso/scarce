import os
import sqlite3
import discord
from discord.ext import commands
import random
import asyncio
from openai import OpenAI

print("RUNNING FILE:", os.path.abspath(__file__))
print("RUNNING SCARCEBOT VERSION 2 - AI MEMORY CODE")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DB_NAME = "scarce_memory.db"

def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            username TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def save_message(user_id, username, channel_id, role, content):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO messages (user_id, username, channel_id, role, content)
        VALUES (?, ?, ?, ?, ?)
    """, (str(user_id), username, str(channel_id), role, content))

    conn.commit()
    conn.close()

def get_recent_memory(channel_id, limit=20):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, role, content
        FROM messages
        WHERE channel_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (str(channel_id), limit))

    rows = cursor.fetchall()
    conn.close()

    rows.reverse()

    memory = []
    for username, role, content in rows:
        memory.append(f"{username} ({role}): {content}")

    return "\n".join(memory)

setup_database()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

normal_statuses = [
    ("listening", "listening to Ninjaman"),
    ("listening", "listening to YoungBoy NeverBrokeAgain"),
    ("watching", "watching scarce chat"),
    ("watching", "thinking about Jiggy"),
    ("watching", "thinking about Sammy"),
    ("watching", "thinking about Curry"),
    ("listening", "listening to Vybz Kartel"),
    ("listening", "listening to Chief Keef")
]

rare_statuses = [
    ("watching", "cleaning up Scarce"),
    ("watching", "doomscrolling TikTok"),
    ("watching", "looking for MightyDuck"),
    ("watching", "hanging with Von"),
    ("watching", "smoking with Chop")
]

async def rotate_status():
    await bot.wait_until_ready()

    while not bot.is_closed():
        status_choice = random.choice(rare_statuses) if random.random() < 0.05 else random.choice(normal_statuses)
        activity_type, text = status_choice

        if activity_type == "playing":
            activity = discord.Game(name=text)
        elif activity_type == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=text)
        elif activity_type == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=text)
        else:
            activity = None

        status_state = random.choice([discord.Status.idle, discord.Status.dnd])
        await bot.change_presence(status=status_state, activity=activity)

        await asyncio.sleep(random.randint(600, 3600))

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    if not hasattr(bot, "status_task_started"):
        bot.status_task_started = True
        bot.loop.create_task(rotate_status())

hype_lines = [
    "SERVER SHAKINGGGGG 🔥🔥🔥",
    "lock in chat 😤",
    "the energy shifting...",
    "Somebody cooking fr 👀",
    "This chat different tonight"
]

jiggy_responses = [
    "Yes that’s his name. Please don’t wear it out.",
    "Stop call mi fada",
    "Put hella BASE in your voice when you're calling a real nigga like jiggy",
    "Jiggy di one and only",
    "If you’re saying jiggy’s name, then it must be for a good reason"
]

hello_responses = [
    "mi deh yah",
    "Gud mawnin",
    "Yow",
    "wah gwan pickney!",
    "wah gwan mi general?",
    "gud evening",
    "yo yo",
    "hey there",
    "wassgud",
    "how are you doing?"
]

@bot.event
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()

    save_message(
        message.author.id,
        message.author.display_name,
        message.channel.id,
        "user",
        message.content
    )

    if random.random() < 0.05:
        async with message.channel.typing():
            await asyncio.sleep(random.randint(2, 5))
            reply = random.choice(hype_lines)
            await message.channel.send(reply)
            save_message(bot.user.id, bot.user.name, message.channel.id, "bot", reply)

    if "jiggy" in content and random.random() < 0.33:
        async with message.channel.typing():
            await asyncio.sleep(random.randint(2, 5))
            reply = random.choice(jiggy_responses)
            await message.channel.send(reply)

    greetings = ["wah gwan mi bredrin", "hey", "yurr"]
    if any(word in content for word in greetings) and random.random() < 0.33:
        async with message.channel.typing():
            await asyncio.sleep(random.randint(2, 5))
            reply = random.choice(hello_responses)
            await message.channel.send(reply)
            save_message(bot.user.id, bot.user.name, message.channel.id, "bot", reply)

    await bot.process_commands(message)

@bot.command(name="ai")
async def ai(ctx, *, prompt: str):
    async with ctx.typing():
        try:
            memory = get_recent_memory(ctx.channel.id, limit=30)

            response = client.responses.create(
                model="gpt-4.1-mini",
                input=f"""
You are ScarceBot, a calm/nuetral bot meant for interation. You rarely reply with more than a sentence unless asked.

Recent channel memory:
{memory}

Current user: {ctx.author.display_name}
Current message: {prompt}

Reply naturally. Keep it under 120 words unless asked for detail.
"""
            )

            answer = response.output_text

            if len(answer) > 1900:
                answer = answer[:1900] + "..."

            await ctx.send(answer)

            save_message(ctx.author.id, ctx.author.display_name, ctx.channel.id, "user", prompt)
            save_message(bot.user.id, bot.user.name, ctx.channel.id, "bot", answer)

        except Exception as e:
            await ctx.send(f"AI error: {e}")

@bot.command()
async def memory(ctx):
    memory_text = get_recent_memory(ctx.channel.id, limit=10)

    if not memory_text:
        await ctx.send("No memory yet.")
    else:
        if len(memory_text) > 1900:
            memory_text = memory_text[:1900] + "..."

        await ctx.send(f"```text\n{memory_text}\n```")

@bot.command()
async def clearmemory(ctx):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM messages
        WHERE channel_id = ?
    """, (str(ctx.channel.id),))

    conn.commit()
    conn.close()

    await ctx.send("Channel memory cleared.")

@bot.command()
async def jiggy(ctx):
    normal_responses = [
        "Jiggy walks in… servers shake and chat bows. 👑 YEAAAAAAAAAHHHHH",
        "man cyan walk pan wata",
        "Big Jiggy, **BIG JIGGY!!!!** YEAAAAHHHHHH",
        "cooking with jiggy...Cooking with jiiiggy...COOKING WITH **JIIIIIIIGGGGGYYYYYYYY!!!!!**"
    ]

    rare_responses = [
        "Jiggy is the glitch in existence — perfection cannot be contained."
    ]

    reply = random.choice(rare_responses) if random.random() < 0.1 else random.choice(normal_responses)
    await ctx.send(reply)
    save_message(bot.user.id, bot.user.name, ctx.channel.id, "bot", reply)

@bot.command()
async def curry(ctx):
    responses = [
        "Marvel Rivals Queen 👑",
        "Curry always had that stallion 🔥"
    ]
    reply = random.choice(responses)
    await ctx.send(reply)
    save_message(bot.user.id, bot.user.name, ctx.channel.id, "bot", reply)

@bot.command(aliases=["samoya"])
async def sammy(ctx):
    responses = [
        "Sammy's #1",
        "https://tenor.com/view/xqc-flex-muscles-overwatch-f%C3%A9lix-lengyel-gif-13473821"
    ]
    reply = random.choice(responses)
    await ctx.send(reply)
    save_message(bot.user.id, bot.user.name, ctx.channel.id, "bot", reply)

@bot.command()
async def kay(ctx):
    reply = "Mi sista Kaaaaaaaay"
    await ctx.send(reply)
    save_message(bot.user.id, bot.user.name, ctx.channel.id, "bot", reply)

@bot.command()
async def kye(ctx):
    reply = "Dats mi BrUdA"
    await ctx.send(reply)
    save_message(bot.user.id, bot.user.name, ctx.channel.id, "bot", reply)

@bot.command()
async def von(ctx):
    responses = [
        "reaaaaaaal badman",
        "he's the real king von"
    ]
    reply = random.choice(responses)
    await ctx.send(reply)
    save_message(bot.user.id, bot.user.name, ctx.channel.id, "bot", reply)

@bot.command()
async def isaa(ctx):
    responses = [
        "Boxing Champion... until Jiggy shows up",
        "Uno 4th Place Seat Warmer"
    ]
    reply = random.choice(responses)
    await ctx.send(reply)
    save_message(bot.user.id, bot.user.name, ctx.channel.id, "bot", reply)

if DISCORD_TOKEN is None:
    raise ValueError("Missing DISCORD_TOKEN environment variable")

if OPENAI_API_KEY is None:
    raise ValueError("Missing OPENAI_API_KEY environment variable")

bot.run(DISCORD_TOKEN)