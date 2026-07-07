import os
import random
import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True

# --- AYARLAR ---
# Buraya stok ekleme yetkisi vermek istediğin rolün ID'sini yapıştır:
YETKILI_ROL_ID = 123456789012345678  # Kendi rol ID'n ile değiştir!

class GeneratorBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        # Stokları kategorilere göre tutan havuz
        self.hesap_deposu = {
            "steam": [],
            "netflix": []
        }

    async def setup_hook(self):
        await self.tree.sync()
        print("Gelişmiş Stok Sistemi senkronize edildi!")

bot = GeneratorBot()

@bot.event
async def on_ready():
    print(f"Generator Bot Aktif: {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="/generate | /stock"))

# ----------------- 1. STOK EKLEME KOMUTU (Sadece Yetkili Rol) -----------------

@bot.hybrid_command(name="stock", description="Depoya yeni hesap ekler (Sadece yetkililer).")
@app_commands.choices(kategori=[
    app_commands.Choice(name="Steam", value="steam"),
    app_commands.Choice(name="Netflix", value="netflix")
])
async def stock(ctx: commands.Context, kategori: str, hesap: str):
    # Komutu yazan kişinin rollerinde bizim belirttiğimiz YETKILI_ROL_ID var mı kontrol ediyoruz
    yetkili_rol = ctx.guild.get_role(YETKILI_ROL_ID)
    
    if yetkili_rol not in ctx.author.roles:
        await ctx.send("❌ Bu komutu kullanmak için gerekli yetkiye sahip değilsiniz!", ephemeral=True)
        return

    # Hesap zaten depoda varsa mükerrer eklemeyi önle
    if hesap in bot.hesap_deposu[kategori]:
        await ctx.send("❌ Bu hesap zaten stokta mevcut!", ephemeral=True)
        return

    # Hesabı ilgili kategoriye ekle
    bot.hesap_deposu[kategori].append(hesap)
    kalan_stok = len(bot.hesap_deposu[kategori])
    
    await ctx.send(f"📥 Başarıyla `{kategori.upper()}` kategorisine 1 yeni hesap eklendi! Toplam Stok: **{kalan_stok}**")

# ----------------- 2. GENERATE KOMUTU (Herkes Kullanabilir) -----------------

@bot.hybrid_command(name="generate", description="Depodan rastgele bir hesap üretir ve DM ile gönderir.")
@app_commands.choices(kategori=[
    app_commands.Choice(name="Steam", value="steam"),
    app_commands.Choice(name="Netflix", value="netflix")
])
async def generate(ctx: commands.Context, kategori: str):
    await ctx.defer()
    
    # Stok kontrolü
    if kategori not in bot.hesap_deposu or len(bot.hesap_deposu[kategori]) == 0:
        await ctx.send(f"❌ Maalesef, `{kategori.upper()}` kategorisinde şu an hiç stok kalmadı!")
        return
        
    # Rastgele hesap seçimi
    secilen_hesap = random.choice(bot.hesap_deposu[kategori])
    
    try:
        # DM Gönderimi
        dm_embed = discord.Embed(
            title="🎁 Hesabınız Başarıyla Üretildi!",
            description=f"İşte talep ettiğiniz `{kategori.upper()}` hesap bilgileri:\n\n`{secilen_hesap}`",
            color=discord.Color.green()
        )
        await ctx.author.send(embed=dm_embed)
        
        # Stoktan silme (görünmez kılma)
        bot.hesap_deposu[kategori].remove(secilen_hesap)
        
        # Sunucuya duyuru mesajı (İsteğin üzerine "real" kelimesini kaldırdım)
        sunucu_embed = discord.Embed(
            title="🎉 BAŞARILI GENERATE!",
            description=f"{ctx.author.mention} az önce başarıyla bir **{kategori.upper()}** hesabı generateledi! 🚀",
            color=discord.Color.blue()
        )
        kalan_stok = len(bot.hesap_deposu[kategori])
        sunucu_embed.set_footer(text=f"Kalan Güncel {kategori.upper()} Stoğu: {kalan_stok}")
        
        await ctx.send(embed=sunucu_embed)
        
    except discord.Forbidden:
        await ctx.send(f"❌ {ctx.author.mention}, DM kutunuz kapalı olduğu için hesabı gönderemedim! Ayarlarınızdan DM'leri açıp tekrar deneyin.")

TOKEN = os.getenv("DISCORD_TOKEN")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("HATA: 'DISCORD_TOKEN' bulunamadı.")
