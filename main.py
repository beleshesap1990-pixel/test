import os
import random
import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True

class GameBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Oyun komutları başarıyla yüklendi!")

bot = GameBot()

# Oyuncu Veritabanı (Şimdilik RAM üzerinde tutuluyor)
# Kullanıcı ID: {"mekan": "Sokak", "envanter": [], "can": 100, "para": 50}
oyuncular = {}

def oyuncu_kontrol(user_id):
    if user_id not in oyuncular:
        oyuncular[user_id] = {
            "mekan": "Karanlık Sokak",
            "envanter": ["Eski Fener"],
            "can": 100,
            "para": 50
        }

@bot.event
async def on_ready():
    print(f"Oyun Botu Çevrimiçi: {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="/kesfet | Açık Dünya RPG"))

# ----------------- OYUN KOMUTLARI -----------------

# 1. Durum / Envanter Komutu
@bot.hybrid_command(name="durum", description="Karakterinizin mevcut durumunu ve envanterini gösterir.")
async def durum(ctx: commands.Context):
    user_id = ctx.author.id
    oyuncu_kontrol(user_id)
    p = oyuncular[user_id]
    
    embed = discord.Embed(title=f"🕵️ {ctx.author.name} - Karakter Durumu", color=discord.Color.dark_red())
    embed.add_field(name="📍 Mevcut Konum", value=f"**{p['mekan']}**", inline=False)
    embed.add_field(name="❤️ Sağlık", value=f"%{p['can']}", inline=True)
    embed.add_field(name="💰 Cüzdan", value=f"{p['para']} $", inline=True)
    
    envanter_listesi = ", ".join(p['envanter']) if p['envanter'] else "Boş"
    embed.add_field(name="🎒 Envanter", value=envanter_listesi, inline=False)
    
    await ctx.send(embed=embed)

# 2. Keşfet / Etrafı Araştır Komutu
@bot.hybrid_command(name="kesfet", description="Bulunduğunuz bölgedeki binaları ve çevreyi araştırın.")
async def kesfet(ctx: commands.Context):
    user_id = ctx.author.id
    oyuncu_kontrol(user_id)
    p = oyuncular[user_id]
    
    # İhtimaller ve atmosferik olaylar
    olaylar = [
        {"tip": "loot", "mesaj": "Terk edilmiş bir dükkana girdin ve tezgâhın altında **Paslı Çakı** ile **20 $** buldun!", "item": "Paslı Çakı", "para": 20, "can": 0},
        {"tip": "loot", "mesaj": "Eski bir deponun kapısını zorlayarak açtın. Kasadan **Şifalı Bitki** çıktı!", "item": "Şifalı Bitki", "para": 0, "can": 0},
        {"tip": "tehlike", "mesaj": "Yıkık bir binaya girerken tavan çöktü! Enkazdan son anda kurtuldun ama hasar aldın.", "item": None, "para": 0, "can": -20},
        {"tip": "bos", "mesaj": "Sokaktaki çöp konteynerlerini ve eski bir arabayı aradın ama işe yarar hiçbir şey bulamadın.", "item": None, "para": 0, "can": 0},
        {"tip": "loot", "mesaj": "Terk edilmiş bir motel odasını aradın. Yatağın altında **Eski bir Mektup** ve **50 $** buldun!", "item": "Eski Mektup", "para": 50, "can": 0}
    ]
    
    secilen_olay = random.choice(olaylar)
    
    # Oyuncu verilerini güncelleme
    if secilen_olay["item"]:
        p["envanter"].append(secilen_olay["item"])
    p["para"] += secilen_olay["para"]
    p["can"] += secilen_olay["can"]
    
    # Can sınır kontrolü
    if p["can"] <= 0:
        p["can"] = 100
        p["envanter"] = ["Eski Fener"]
        p["para"] = max(0, p["para"] - 30)
        p["mekan"] = "Güvenli Sığınak"
        
        embed = discord.Embed(title="💀 Öldün!", description="Sağlığın sıfıra düştü. Uyandığında üstündeki çoğu şeyi kaybetmiştin ve kendini **Güvenli Sığınak**'ta buldun.", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    # Normal sonuç ekranı
    renk = discord.Color.green() if secilen_olay["tip"] == "loot" else (discord.Color.red() if secilen_olay["tip"] == "tehlike" else discord.Color.light_grey())
    
    embed = discord.Embed(title="🔍 Çevreyi Araştırıyorsun...", description=secilen_olay["mesaj"], color=renk)
    await ctx.send(embed=embed)

# 3. Mekan Değiştirme Komutu
@bot.hybrid_command(name="git", description="Farklı bir bölgeye veya binaya geçiş yapın.")
async def git(ctx: commands.Context, mekan: str):
    user_id = ctx.author.id
    oyuncu_kontrol(user_id)
    
    # Oyuncunun gidebileceği mekan örnekleri
    Mekanlar = ["Karanlık Sokak", "Terk Edilmiş Depo", "Eski Otel", "Güvenli Sığınak", "Merkez İstasyon"]
    
    if mekan not in mekanlar:
        temiz_mekanlar = ", ".join([f"`{m}`" for m in mekanlar])
        await ctx.send(f"❌ Bilinmeyen bir yere gitmeye çalışıyorsun. Gidebileceğin yerler: {temiz_mekanlar}")
        return
        
    oyuncular[user_id]["mekan"] = mekan
    await ctx.send(f"🏃‍♂️ {ctx.author.mention}, başarıyla **{mekan}** bölgesine geçiş yaptın. Etrafı keşfetmeye başlayabilirsin!")

TOKEN = os.getenv("DISCORD_TOKEN")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("HATA: 'DISCORD_TOKEN' eksik.")
