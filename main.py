import os
import random
import json
import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True

# --- RAILWAY DEĞİŞKENİ KONTROLÜ ---
# Kod, Railway panelindeki YETKILI_ROL_ID değişkenini buradan çeker.
# Eğer bulamazsa hata vermemesi için varsayılan olarak 0 atar.
try:
    YETKILI_ROL_ID = int(os.getenv("YETKILI_ROL_ID", 0))
except ValueError:
    print("HATA: Railway panelindeki YETKILI_ROL_ID bir sayı olmalıdır!")
    YETKILI_ROL_ID = 0

DOSYA_ADI = "stoklar.txt"

class GeneratorBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.hesap_deposu = self.stoklari_yukle()

    # Stokları kalıcı dosyadan okuma fonksiyonu
    def stoklari_yukle(self):
        if os.path.exists(DOSYA_ADI):
            try:
                with open(DOSYA_ADI, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"steam": [], "netflix": []}
        return {"steam": [], "netflix": []}

    # Stokları kalıcı dosyaya kaydetme fonksiyonu
    def stoklari_kaydet(self):
        try:
            with open(DOSYA_ADI, "w", encoding="utf-8") as f:
                json.dump(self.hesap_deposu, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Dosya kaydedilirken hata oluştu: {e}")

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Kalıcı Stok Sistemi ve Yetkili ID ({YETKILI_ROL_ID}) aktif!")

bot = GeneratorBot()

@bot.event
async def on_ready():
    print(f"Generator Bot Aktif: {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="/generate | /stock"))

# ----------------- 1. STOK EKLEME KOMUTU (Sadece Yetkili Rol) -----------------

@bot.hybrid_command(name="stock", description="Depoya yeni hesap ekler (Kalıcıdır).")
@app_commands.choices(kategori=[
    app_commands.Choice(name="Steam", value="steam"),
    app_commands.Choice(name="Netflix", value="netflix")
])
async def stock(ctx: commands.Context, kategori: str, hesap: str):
    # Railway'den gelen ID'ye sahip rolü sunucudan buluyoruz
    yetkili_rol = ctx.guild.get_role(YETKILI_ROL_ID)
    
    # Rol kontrolü
    if YETKILI_ROL_ID == 0 or yetkili_rol not in ctx.author.roles:
        await ctx.send("❌ Bu komutu kullanmak için Railway'de tanımlı yetkili role sahip olmalısınız!", ephemeral=True)
        return

    if hesap in bot.hesap_deposu[kategori]:
        await ctx.send("❌ Bu hesap zaten stokta mevcut!", ephemeral=True)
        return

    # Hesabı ekle ve DOSYAYA KAYDET
    bot.hesap_deposu[kategori].append(hesap)
    bot.stoklari_kaydet()
    
    kalan_stok = len(bot.hesap_deposu[kategori])
    await ctx.send(f"📥 Başarıyla `{kategori.upper()}` kategorisine 1 yeni hesap eklendi! Toplam Güncel Stok: **{kalan_stok}**")

# ----------------- 2. GENERATE KOMUTU (Herkes Kullanabilir) -----------------

@bot.hybrid_command(name="generate", description="Depodan rastgele bir hesap üretir, DM atar ve stoktan siler.")
@app_commands.choices(kategori=[
    app_commands.Choice(name="Steam", value="steam"),
    app_commands.Choice(name="Netflix", value="netflix")
])
async def generate(ctx: commands.Context, kategori: str):
    await ctx.defer()
    
    if kategori not in bot.hesap_deposu or len(bot.hesap_deposu[kategori]) == 0:
        await ctx.send(f"❌ Maalesef, `{kategori.upper()}` kategorisinde şu an hiç stok kalmadı!")
        return
        
    secilen_hesap = random.choice(bot.hesap_deposu[kategori])
    
    try:
        dm_embed = discord.Embed(
            title="🎁 Hesabınız Başarıyla Üretildi!",
            description=f"İşte talep ettiğiniz `{kategori.upper()}` hesap bilgileri:\n\n`{secilen_hesap}`",
            color=discord.Color.green()
        )
        await ctx.author.send(embed=dm_embed)
        
        # Stoktan sil ve YENİ HALİNİ DOSYAYA KAYDET
        bot.hesap_deposu[kategori].remove(secilen_hesap)
        bot.stoklari_kaydet()
        
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
