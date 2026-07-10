import os
import random
import json
import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True

try:
    YETKILI_ROL_ID = int(os.getenv("YETKILI_ROL_ID", 0))
except ValueError:
    print("ERROR: YETKILI_ROL_ID in the Railway panel must be a valid number!")
    YETKILI_ROL_ID = 0

DOSYA_ADI = "stoklar.txt"

class GeneratorBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.hesap_deposu = self.stoklari_yukle()

    def stoklari_yukle(self):
        if os.path.exists(DOSYA_ADI):
            try:
                with open(DOSYA_ADI, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {} # Dynamic database starts empty

    def stoklari_kaydet(self):
        try:
            with open(DOSYA_ADI, "w", encoding="utf-8") as f:
                json.dump(self.hesap_deposu, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving file: {e}")

    async def setup_hook(self):
        await self.tree.sync()
        print(f"System active! Authorized Role ID: {YETKILI_ROL_ID}")

bot = GeneratorBot()

@bot.event
async def on_ready():
    print(f"Generator Bot is Online: {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="/stock | /generate"))

# ----------------- 1. ADD STOCK COMMAND -----------------

@bot.hybrid_command(name="add-stock", description="Add accounts to the stock (Single or bulk using '/' separator).")
async def add_stock(ctx: commands.Context, category: str, accounts: str):
    authorized_role = ctx.guild.get_role(YETKILI_ROL_ID)
    category = category.lower().strip()
    
    if YETKILI_ROL_ID == 0 or authorized_role not in ctx.author.roles:
        await ctx.send("❌ You must have the authorized role to use this command!", ephemeral=True)
        return

    # Create category dynamically if it doesn't exist
    if category not in bot.hesap_deposu:
        bot.hesap_deposu[category] = []

    raw_list = accounts.split("/")
    added_count = 0

    for acc in raw_list:
        clean_acc = acc.strip()
        if not clean_acc:
            continue
        if clean_acc not in bot.hesap_deposu[category]:
            bot.hesap_deposu[category].append(clean_acc)
            added_count += 1

    if added_count > 0:
        bot.stoklari_kaydet()

    await ctx.send(f"✅ Successfully added **{added_count}** new account(s) to `{category.upper()}` category!")

# ----------------- 2. CHECK STOCK STATUS PANEL -----------------

@bot.hybrid_command(name="stock", description="List the current status of active stock categories.")
async def stock(ctx: commands.Context):
    embed = discord.Embed(
        title="📦 Normal Stock Status",
        color=discord.Color.green()
    )
    
    stock_text = ""
    active_categories = 0

    for cat, accounts_list in bot.hesap_deposu.items():
        stock_count = len(accounts_list)
        
        # IF STOCK IS 0, HIDE IT FROM THE LIST
        if stock_count == 0:
            continue
            
        active_categories += 1
        
        # Dynamic Emoji Indicator
        if stock_count <= 10:
            emoji = "🟡"  # Low stock
        else:
            emoji = "🟢"  # Plenty of stock

        stock_text += f"{emoji} **{cat.capitalize()}**: {stock_count}\n"

    if active_categories == 0:
        embed.description = "❌ There is currently no active stock available in the database."
    else:
        embed.description = stock_text

    embed.add_field(
        name="📊 Legend", 
        value="🟡 Accounts are nearly out of stock\n🟢 There is plenty of stock", 
        inline=False
    )
    embed.set_footer(text="Bot was made by real.11")
    
    await ctx.send(embed=embed)

# ----------------- 3. GENERATE ACCOUNT COMMAND -----------------

@bot.hybrid_command(name="generate", description="Generate a random account from the stock and receive it via DM.")
async def generate(ctx: commands.Context, category: str):
    await ctx.defer()
    category = category.lower().strip()
    
    if category not in bot.hesap_deposu or len(bot.hesap_deposu[category]) == 0:
        await ctx.send(f"❌ Sorry, the `{category.upper()}` category is currently out of stock!")
        return
        
    selected_account = random.choice(bot.hesap_deposu[category])
    
    try:
        dm_embed = discord.Embed(
            title="🎁 Your Account Has Been Generated!",
            description=f"Here is your requested `{category.upper()}` account details:\n\n`{selected_account}`",
            color=discord.Color.green()
        )
        await ctx.author.send(embed=dm_embed)
        
        bot.hesap_deposu[category].remove(selected_account)
        bot.stoklari_kaydet()
        
        server_embed = discord.Embed(
            title="🎉 GENERATE SUCCESSFUL!",
            description=f"{ctx.author.mention} just successfully generated a **{category.upper()}** account! 🚀",
            color=discord.Color.blue()
        )
        await ctx.send(embed=server_embed)
        
    except discord.Forbidden:
        await ctx.send(f"❌ {ctx.author.mention}, I couldn't send the account because your DMs are closed!")

# ----------------- 4. MADE BY COMMAND -----------------

@bot.hybrid_command(name="madeby", description="Show the creator of the bot.")
async def madeby(ctx: commands.Context):
    await ctx.send("🛡️ This bot was made by **real.11**")

TOKEN = os.getenv("DISCORD_TOKEN")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("ERROR: 'DISCORD_TOKEN' environment variable not found.")
