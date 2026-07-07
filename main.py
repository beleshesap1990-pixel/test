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

# Listendeki tüm popüler kategorileri buraya tanımladım. Başlangıçta hepsi boş başlar.
KATEGORILER = [
    "amazon", "amazoncard", "azure", "bestbuycard", "blockchain", "callofduty", 
    "canal", "canva", "cc", "coinbase", "crunchyroll", "dazn", "deezer", "dhl", 
    "discord", "discordtoken", "disney", "dropbox", "ebay", "epicgames", 
    "expressvpn", "facebook", "fedex", "funimation", "garena", "gmail", 
    "hanimetv", "hbomax", "hotmail", "hulu", "ign", "instacart", "instagram", 
    "krunker", "linkedin", "microsoft", "minecraft", "mix", "mixcloud", 
    "netflix", "nintendo", "nitroboostpromo", "nitrocc", "nitrocode", 
    "nordvpn", "outlook", "pandora", "paramount+", "paypal", "pes", 
    "pinterest", "playstation", "playstore", "prime", "protonvpn", 
    "psncode", "pubg", "razer", "rblx2010", "rblx2017", "rblx2018", 
    "rblxgiftcard", "rblxoffsale", "reddit", "roblox", "robloxcookie", 
    "rockstar", "sephora", "shopify", "snapchat", "sony", "soundcloud", 
    "spotify", "stake", "star+", "steam", "target", "targetcard", "tidal", 
    "tiktok", "tinder", "tradingview", "tumblr", "twitch", "twitchtoken", 
    "twitter", "ubereats", "valorant", "walmart", "winscribe", "yahoo", "youtube"
]

class GeneratorBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.hesap_deposu = self.stoklari_yukle()

    def stoklari_yukle(self):
        if os.path.exists(DOSYA_ADI):
            try:
                with open(DOSYA_ADI, "r", encoding="utf-8") as f:
                    veriler = json.load(f)
                    # Eksik kategoriler varsa tamamla
                    for kat in KATEGORILER:
                        if kat not in veriler:
                            veriler[kat] = []
                    return veriler
            except Exception:
                pass
        return {kat: [] for kat in KATEGORILER}

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

# ----------------- 1. REORGANİZE: STOK EKLEME KOMUTU -----------------

@bot.hybrid_command(name="stock-ekle", description="Depoya tekli veya aralarına '/' koyarak toplu hesap ekler.")
async def stock_ekle(ctx: commands.Context, kategori: str, hesaplar: str):
    yetkili_rol = ctx.guild.get_role(YETKILI_ROL_ID)
    kategori = kategori.lower().strip()
    
    if YETKILI_ROL_ID == 0 or yetkili_rol not in ctx.author.roles:
        await ctx.send("❌ Bu komutu kullanmak için yetkili role sahip olmalısınız!", ephemeral=True)
        return

    if kategori not in bot.hesap_deposu:
        await ctx.send(f"❌ `{kategori}` adında bir kategori sistemde bulunamadı!", ephemeral=True)
        return

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

# ----------------- 2. YENİ: STOK DURUMUNU KONTROL ETME PANELİ -----------------

@bot.hybrid_command(name="stock", description="Tüm kategorilerin güncel stok durumunu listeler.")
async def stock(ctx: commands.Context):
    embed = discord.Embed(
        title="📦 Operator Stock Status",
        color=discord.Color.blurple()
    )
    
    stok_metni = ""
    # Tüm kategorileri dönüp stok durumuna göre emoji belirliyoruz
    for kat, hesaplar in bot.hesap_deposu.items():
        stok_sayisi = len(hesaplar)
        
        if stok_sayisi == 0:
            emoji = "🔴"  # Out of stock
        elif stok_sayisi <= 10:
            emoji = "🟡"  # Nearly out of stock
        else:
            emoji = "🟢"  # Plenty of stock
            
        stok_metni += f"{emoji} **{kat.capitalize()}**: {stok_sayisi}\n"

    # Discord tek embed alanında 4096 karakter sınırına sahip. 
    # Yazı çok uzun olursa taşmasın diye gerekirse bölerek ekliyoruz.
    if len(stok_metni) > 2000:
        parcalar = [stok_metni[i:i+1900] for i in range(0, len(stok_metni), 1900)]
        embed.description = parcalar[0]
        # Eğer sığmadıysa field olarak devamını ekle
        if len(parcalar) > 1:
            embed.add_field(name="Devamı", value=parcalar[1], inline=False)
    else:
        embed.description = stok_metni

    # İstediğin açıklama alt bilgi (footer) alanları
    embed.add_field(
        name="📊 Legend", 
        value="🔴 Accounts are completely out of stock\n🟡 Accounts are nearly out of stock\n🟢 There is plenty of stock", 
        inline=False
    )
    embed.set_footer(text="Bot was made by real.11") # İmzanı korudum
    
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
        
        sunucu_embed = discord.Embed(
            title="🎉 BAŞARILI GENERATE!",
            description=f"{ctx.author.mention} az önce başarıyla bir **{kategori.upper()}** hesabı generateledi! 🚀",
            color=discord.Color.blue()
        )
        await ctx.send(embed=sunucu_embed)
        
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
