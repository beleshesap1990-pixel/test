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
    print("HATA: Railway panelindeki YETKILI_ROL_ID bir sayı olmalıdır!")
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
                return {"steam": [], "netflix": []}
        return {"steam": [], "netflix": []}

    def stoklari_kaydet(self):
        try:
            with open(DOSYA_ADI, "w", encoding="utf-8") as f:
                json.dump(self.hesap_deposu, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Dosya kaydedilirken hata oluştu: {e}")

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Sistem ve Yetkili ID ({YETKILI_ROL_ID}) aktif!")

bot = GeneratorBot()

@bot.event
async def on_ready():
    print(f"Generator Bot Aktif: {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="/generate | /stock"))

# ----------------- 1. TOPLU STOK EKLEME KOMUTU -----------------

@bot.hybrid_command(name="stock", description="Depoya tekli veya aralarına '/' koyarak toplu hesap ekler.")
@app_commands.choices(kategori=[
    app_commands.Choice(name="Steam", value="steam"),
    app_commands.Choice(name="Netflix", value="netflix")
])
async def stock(ctx: commands.Context, kategori: str, hesaplar: str):
    yetkili_rol = ctx.guild.get_role(YETKILI_ROL_ID)
    
    if YETKILI_ROL_ID == 0 or yetkili_rol not in ctx.author.roles:
        await ctx.send("❌ Bu komutu kullanmak için yetkili role sahip olmalısınız!", ephemeral=True)
        return

    # Gelen metni "/" işaretine göre parçalara ayırıyoruz
    # strip() ile sağındaki solundaki boşlukları temizliyoruz
    ham_liste = hesaplar.split("/")
    eklenen_sayisi = 0
    mevcut_sayisi = 0

    for h in ham_liste:
        temiz_hesap = h.strip()
        if not temiz_hesap:  # Eğer boşluk kaldıysa atla
            continue
            
        # Hesap zaten depoda yoksa ekle
        if temiz_hesap not in bot.hesap_deposu[kategori]:
            bot.hesap_deposu[kategori].append(temiz_hesap)
            eklenen_sayisi += 1
        else:
            mevcut_sayisi += 1

    # Eğer en az 1 hesap eklendiyse dosyayı güncelle
    if eklenen_sayisi > 0:
        bot.stoklari_kaydet()

    kalan_stok = len(bot.hesap_deposu[kategori])
    
    # Şık bir bilgilendirme mesajı verelim
    mesaj = f"📥 **Stok İşlemi Tamamlandı!** ({kategori.upper()})\n"
    mesaj += f"✅ Başarıyla eklenen yeni hesap: **{eklenen_sayisi}**\n"
    if mevcut_sayisi > 0:
        mesaj += f"⚠️ Zaten stokta olduğu için atlanan: **{mevcut_sayisi}**\n"
    mesaj += f"📦 Toplam Güncel Stok: **{kalan_stok}**"
    
    await ctx.send(mesaj)

# ----------------- 2. GENERATE KOMUTU -----------------

@bot.hybrid_command(name="generate", description="Depodan rastgele bir hesap üretir, DM atar.")
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
        await ctx.send(f"❌ {ctx.author.mention}, DM kutunuz kapalı olduğu için hesabı gönderemedim!")

# ----------------- 3. MADE BY KOMUTU -----------------

@bot.hybrid_command(name="madeby", description="botun yapımcısını gösterir")
async def madeby(ctx: commands.Context):
    await ctx.send("🛡️made by **real.11**")

TOKEN = os.getenv("DISCORD_TOKEN")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("HATA: 'DISCORD_TOKEN' bulunamadı.")
