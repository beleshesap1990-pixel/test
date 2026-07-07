import os
import discord
from discord.ext import commands, tasks
import aiohttp

intents = discord.Intents.default()
intents.message_content = True

class CryptoBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        # Arka planda fiyat ve alarm takibini başlatır
        self.fiyat_takip.start()
        print("Kripto Radar komutları ve takip mekanizması aktif!")

bot = CryptoBot()

# Alarm kurulu kanalların listesi (Sunucu_ID: Kanal_ID)
alarm_kanallari = {}

@bot.event
async def on_ready():
    print(f"Kripto Botu Giriş Yaptı: {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="/kripto | Canlı Takip"))

# ----------------- ARKA PLAN CANLI TAKİP GÖREVİ -----------------
# Her 60 saniyede bir çalışır ve fiyat anomalilerini/büyük hareketleri inceler
@tasks.loop(seconds=60)
async def fiyat_takip():
    async with aiohttp.ClientSession() as session:
        # Ücretsiz ve anahtarsız CoinGecko API'sini kullanarak Solana ve Bitcoin fiyatını çekiyoruz
        url = "https://api.coingecko.com/api/v3/simple/price?ids=solana,bitcoin&vs_currencies=usd&include_24hr_change=true"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.text()
                    # İleride buraya: "Eğer SOL fiyatı %5 birden düşerse/yükselirse alarm kanallarına mesaj at" 
                    # gibi balina ve anomali filtreleri eklenecek.
        except Exception as e:
            print(f"API bağlantı hatası: {e}")

# ----------------- KULLANICI KOMUTLARI -----------------

# 1. Anlık Fiyat Sorgulama (Herkes Kullanabilir)
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
                    embed.add_field(
                        name="🟣 Solana (SOL)", 
                        value=f"Fiyat: **${sol_fiyat:,}**\n24s Değişim: `%{sol_degisim:.2f}`", 
                        inline=False
                    )
                    embed.add_field(
                        name="🟠 Bitcoin (BTC)", 
                        value=f"Fiyat: **${btc_fiyat:,}**\n24s Değişim: `%{btc_degisim:.2f}`", 
                        inline=False
                    )
                    embed.set_footer(text="Veriler anlık olarak güncellenmektedir.")
                    
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Kripto fiyat verileri şu an çekilemiyor, lütfen az sonra tekrar deneyin.")
        except Exception as e:
            await ctx.send(f"❌ Sistem hatası: {e}")

# 2. VIP Alarm Kanalı Belirleme (Para Kazanma Komutun)
@bot.hybrid_command(name="alarm-kanali-ayarla", description="Balina ve ani fiyat hareketleri alarmlarının düşeceği kanalı seçer.")
@commands.has_permissions(administrator=True)
async def alarm_ayarla(ctx: commands.Context, kanal: discord.TextChannel):
    sunucu_id = ctx.guild.id
    # Gerçek projede bu sunucunun premium süresi dolmuş mu diye kontrol edilir
    alarm_kanallari[sunucu_id] = kanal.id
    await ctx.send(f"🚀 Başarılı! **Premium Balina ve Sinyal Alarmları** artık {kanal.mention} kanalına anlık gönderilecek.")

# 3. Satış Paneli
@bot.hybrid_command(name="vip-satinal", description="Premium sinyal ve balina takibi aboneliği hakkında bilgi verir.")
async def vip_satinal(ctx: commands.Context):
    embed = discord.Embed(
        title="👑 Kripto Radar VIP Üyelik", 
        description="Sunucunuzu profesyonel bir işlem merkezine dönüştürün!", 
        color=discord.Color.gold()
    )
    embed.add_field(name="💰 Aylık Abonelik", value="**$19.99 / Ay**", inline=True)
    embed.add_field(name="⚡ Dahil Olan Özellikler", value="• 7/24 Canlı Solana Balina Cüzdan Takibi\n• Ani %3 üzeri hacim girişlerinde otomatik panik alarmları\n• Premium üyelere özel RSI indikatör sinyalleri", inline=False)
    embed.add_field(name="🛒 Ödeme Kanalı", value="[Abonelik Başlatmak İçin Tıkla](https://shop.beleshesap1990-pixel.com) (Örnektir)", inline=False)
    await ctx.send(embed=embed)

TOKEN = os.getenv("DISCORD_TOKEN")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("HATA: 'DISCORD_TOKEN' eksik.")
