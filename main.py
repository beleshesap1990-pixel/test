import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
from utils.database import Database
from utils.logger import BotLogger

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.db = Database()
bot.bot_logger = BotLogger()

COGS = [
    "cogs.hiring",
    "cogs.reputation",
    "cogs.moderation",
    "cogs.logging",
    "cogs.profiles",
]

@bot.event
async def on_ready():
    await bot.db.init()
    await bot.tree.sync()
    print(f"✅ Bot aktif: {bot.user} | {len(bot.guilds)} sunucu")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Bu komutu kullanmak için yetkin yok.", ephemeral=True)

async def main():
    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)
        await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())
