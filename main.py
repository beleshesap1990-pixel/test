import os
import discord
from discord.ext import commands
from discord import app_commands

# Discord Intent ayarları (Mesajlaşma ve sunucu etkileşimleri için)
intents = discord.Intents.default()
intents.message_content = True

# Hem klasik metin komutları hem de Slash komutları destekleyen hibrit yapı
class HybridBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Yazdığımız Slash komutlarını Discord API'sine kaydeder (Senkronize eder)
        await self.tree.sync()
        print("Slash komutları başarıyla senkronize edildi!")

bot = HybridBot()

@bot.event
async def on_ready():
    print(f"Bot olarak giriş yapıldı: {bot.user.name} (ID: {bot.user.id})")
    # Botun durum açıklamasını ayarlıyoruz
    await bot.change_presence(activity=discord.Game(name="/yardim | Ekonomi & Para"))

# ----------------- HİBRİT KOMUTLAR (Para / Ekonomi Örnekleri) -----------------

# 1. Klasik Yardım Komutu
@bot.hybrid_command(name="yardim", description="Botun tüm komutlarını listeler.")
async def yardim(ctx: commands.Context):
    embed = discord.Embed(
        title="💰 Para & Ekonomi Botu Komutları", 
        description="İşte kullanabileceğiniz bazı temel komutlar:",
        color=discord.Color.green()
    )
    embed.add_field(name="/cuzdan", value="Mevcut bakiyenizi gösterir.", inline=False)
    embed.add_field(name="/gunluk", value="Günlük giriş ödülünüzü alırsınız.", inline=False)
    embed.set_footer(text="Geliştirme aşamasındadır.")
    await ctx.send(embed=embed)

# 2. Bakiye Sorgulama (Örnek Mantık)
@bot.hybrid_command(name="cuzdan", description="Mevcut bakiyenizi ve kazançlarınızı gösterir.")
async def cuzdan(ctx: commands.Context):
    # İleride buraya veritabanı veya kripto API entegrasyonu gelecek
    bakiye = 1500  # Geçici statik değer
    await ctx.send(f"💳 {ctx.author.mention}, mevcut bakiyeniz: **${bakiye}**")

# 3. Günlük Ödül Komutu
@bot.hybrid_command(name="gunluk", description="Günlük ücretsiz ödülünüzü talep edin.")
async def gunluk(ctx: commands.Context):
    odul = 250
    await ctx.send(f"🎉 Tebrikler {ctx.author.mention}! Günlük ödülünüz olan **${odul}** hesabınıza eklendi.")

# Railway üzerindeki Çevre Değişkenlerinden (Environment Variables) Token'ı çeker
TOKEN = os.getenv("DISCORD_TOKEN")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("HATA: 'DISCORD_TOKEN' çevre değişkeni bulunamadı! Lütfen Railway panelinden ekleyin.")
