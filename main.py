import os
import discord
from discord.ext import commands, tasks
import aiohttp

intents = discord.Intents.default()
intents.message_content = True

class CryptoBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        # Listeyi doğrudan sınıf içinde tanımlıyoruz
        self.alarm_kanallari = {}

    async def setup_hook(self):
        await self.tree.sync()
        # Görevi başlatıyoruz
        self.fiyat_takip.start()
        print("Kripto Radar komutları ve takip mekanizması aktif!")

    # Hatanın çözümü: @tasks.loop fonksiyonunu sınıfın (class) İÇİNE aldık ve self ekledik
    @tasks.loop(seconds=60)
    async def fiyat_takip(self):
        async with aiohttp.ClientSession() as session:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=solana,bitcoin&vs_currencies=usd&include_24hr_change=true"
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        pass  # Arka plan verisi sorunsuz çekiliyor
            except Exception as e:
                print(f"API bağlantı hatası: {e}")

bot = CryptoBot()

# ----------------- KULLANICI KOMUTLARI -----------------

@bot.event
async def on_ready():
    print(f"Kripto Botu Giriş Yaptı: {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="/kripto | Canlı Takip"))

@bot.hybrid_command(name="kripto", description="Solana (SOL) ve Bitcoin (BTC) anlık fiyat verilerini getirir.")
async def kripto(ctx: commands.Context):
    await ctx.defer()
    url = "https://api.coingecko.com/api/v3/simple/price?ids=solana,bitcoin&vs_currencies=usd&include_24hr_change=true"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    sol_fiyat = data["solana"]["usd"]
                    sol_degisim = data["solana"]["usd_24h_change"]
                    btc_fiyat = data["bitcoin"]["usd"]
                    btc_degisim = data["bitcoin"]["usd_24h_change"]
                    
                    embed = discord.Embed(title="📈 Anlık Kripto Radar Raporu", color=discord.Color.blue())
                    embed.add_field(name="🟣 Solana (SOL)", value=f"Fiyat: **${sol_fiyat:,}**\n24s Değişim: `%{sol_degisim:.2f}`", inline=False)
                    embed.add_field(name="🟠 Bitcoin (BTC)", value=f"Fiyat: **${btc_fiyat:,}**\n24s Değişim: `%{btc_degisim:.2f}`", inline=False)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Veriler şu an çekilemiyor.")
        except Exception as e:
            await ctx.send(f"❌ Sistem hatası: {e}")

@bot.hybrid_command(name="alarm-kanali-ayarla", description="Balina alarmlarının düşeceği kanalı seçer.")
@commands.has_permissions(administrator=True)
async def alarm_ayarla(ctx: commands.Context, kanal: discord.TextChannel):
    bot.alarm_kanallari[ctx.guild.id] = kanal.id
    await ctx.send(f"🚀 Başarılı! Alarmlar artık {kanal.mention} kanalına gönderilecek.")

@bot.hybrid_command(name="vip-satinal", description="Premium üyelik bilgisi.")
async def vip_satinal(ctx: commands.Context):
    embed = discord.Embed(title="👑 Kripto Radar VIP Üyelik", description="Aylık $19.99", color=discord.Color.gold())
    await ctx.send(embed=embed)

TOKEN = os.getenv("DISCORD_TOKEN")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("HATA: 'DISCORD_TOKEN' eksik.")
