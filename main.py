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
                pass
        return {} # Başlangıçta tamamen boş veri tabanı

    def stoklari_kaydet(self):
        try:
            with open(DOSYA_ADI, "w", encoding="utf-8") as f:
                json.dump(self.hesap_deposu, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Dosya kaydedilirken hata oluştu: {e}")

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Sistem aktif! Yetkili ID: {YETKILI_ROL_ID}")

bot = GeneratorBot()

@bot.event
async def on_ready():
    print(f"Generator Bot Aktif: {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="/stock | /generate"))

# ----------------- 1. STOK EKLEME KOMUTU -----------------

@bot.hybrid_command(name="stock-ekle", description="Depoya tekli veya aralarına '/' koyarak toplu hesap ekler.")
async def stock_ekle(ctx: commands.Context, kategori: str, hesaplar: str):
    yetkili_rol = ctx.guild.get_role(YETKILI_ROL_ID)
    kategori = kategori.lower().strip()
    
    if YETKILI_ROL_ID == 0 or yetkili_rol not in ctx.author.roles:
        await ctx.send("❌ Bu komutu kullanmak için yetkili role sahip olmalısınız!", ephemeral=True)
        return

    # Eğer kategori veritabanında yoksa dinamik olarak oluşturulur
    if kategori not in bot.hesap_deposu:
        bot.hesap_deposu[kategori] = []

    ham_liste = hesaplar.split("/")
    eklenen_sayisi = 0

    for h in ham_liste:
        temiz_hesap = h.strip()
        if not temiz_hesap:
            continue
        if temiz_hesap not in bot.hesap_deposu[kategori]:
            bot.hesap_deposu[kategori].append(temiz_hesap)
            eklenen_sayisi += 1

    if eklenen_sayisi > 0:
        bot.stoklari_kaydet()

    await ctx.send(f"✅ `{kategori.upper()}` kategorisine **{eklenen_sayisi}** adet yeni hesap başarıyla eklendi!")

# ----------------- 2. KONTROL ETME PANELİ (Sadece Mevcut Stoklar) -----------------

@bot.hybrid_command(name="stock", description="Mevcut kategorilerin güncel stok durumunu listeler.")
async def stock(ctx: commands.Context):
    embed = discord.Embed(
        title="📦 Normal Stock Status",
        color=discord.Color.green()
    )
    
    stok_metni = ""
    aktif_kategori_sayisi = 0

    # Sadece içinde en az 1 hesap olan veya geçmişte eklenmiş kategorileri kontrol et
    for kat, hesaplar in bot.hesap_deposu.items():
        stok_sayisi = len(hesaplar)
        
        # EĞER STOK 0 İSE LİSTEDE GÖSTERME, PAS GEÇ
        if stok_sayisi == 0:
            continue
            
        aktif_kategori_sayisi += 1
        
        # Dinamik Emoji Ayarı
        if stok_sayisi <= 10:
            emoji = "🟡"  # Azalıyor
        else:
            emoji = "🟢"  # Bolca var

        stok_metni += f"{emoji} **{kat.capitalize()}**: {stok_sayisi}\n"

    # Eğer hiçbir kategoride hiç stok yoksa kullanıcıyı bilgilendir
    if aktif_kategori_sayisi == 0:
        embed.description = "❌ Şu anda sunucuda aktif hiçbir stok bulunmamaktadır."
    else:
        embed.description = stok_metni

    embed.add_field(
        name="📊 Legend", 
        value="🟡 Accounts are nearly out of stock\n🟢 There is plenty of stock", 
        inline=False
    )
    embed.set_footer(text="Bot was made by real.11")
    
    await ctx.send(embed=embed)

# ----------------- 3. GENERATE KOMUTU -----------------

@bot.hybrid_command(name="generate", description="Depodan rastgele bir hesap üretir, DM atar.")
async def generate(ctx: commands.Context, kategori: str):
    await ctx.defer()
    kategori = kategori.lower().strip()
    
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
        
        sunu_embed = discord.Embed(
            title="🎉 BAŞARILI GENERATE!",
            description=f"{ctx.author.mention} az önce başarıyla bir **{kategori.upper()}** hesabı generateledi! 🚀",
            color=discord.Color.blue()
        )
        await ctx.send(embed=sunu_embed)
        
    except discord.Forbidden:
        await ctx.send(f"❌ {ctx.author.mention}, DM kutunuz kapalı olduğu için hesabı gönderemedim!")

# ----------------- 4. MADE BY KOMUTU -----------------

@bot.hybrid_command(name="madeby", description="Botun yapımcısını gösterir.")
async def madeby(ctx: commands.Context):
    await ctx.send("🛡️made by **real.11**")

TOKEN = os.getenv("DISCORD_TOKEN")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("HATA: 'DISCORD_TOKEN' bulunamadı.")
