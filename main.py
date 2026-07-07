import os
import random
import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True

class GeneratorBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        
        # ----------------- HESAP DEPOSU (STOKLAR) -----------------
        # İstediğin kadar hesabı buraya "kullaniciadi:sifre" formatında ekleyebilirsin.
        # Gerçek projede bot kapandığında silinmemesi için burası veritabanına bağlanır.
        self.hesap_deposu = {
            "steam": [
                "steam_user1:sifre123",
                "steam_gamer99:pass456",
                "pro_playerX:steam789"
            ],
            "netflix": [
                "premium1@gmail.com:net123",
                "dizi_izle@gmail.com:flix456"
            ]
        }

    async def setup_hook(self):
        await self.tree.sync()
        print("Generator sistemi başarıyla senkronize edildi!")

bot = GeneratorBot()

@bot.event
async def on_ready():
    print(f"Generator Bot Aktif: {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="/generate | Hesap Dağıtıcı"))

# ----------------- GENERATE KOMUTU -----------------

@bot.hybrid_command(name="generate", description="Depodan rastgele bir hesap üretir ve DM ile gönderir.")
@app_commands.choices(kategori=[
    app_commands.Choice(name="Steam", value="steam"),
    app_commands.Choice(name="Netflix", value="netflix")
])
async def generate(ctx: commands.Context, kategori: str):
    # Botun işlem yaptığını belirtmek için mesajı beklemeye alıyoruz
    await ctx.defer()
    
    # Kategorinin depoda olup olmadığını ve stok kontrolünü yapıyoruz
    if kategori not in bot.hesap_deposu or len(bot.hesap_deposu[kategori]) == 0:
        await ctx.send(f"❌ Maalesef, `{kategori}` kategorisinde şu an hiç stok kalmadı!")
        return
        
    # Depodan rastgele bir hesap seçiyoruz
    secilen_hesap = random.choice(bot.hesap_deposu[kategori])
    
    try:
        # 1. Kullanıcıya hesabı DM (Özel Mesaj) yoluyla gönderiyoruz
        dm_embed = discord.Embed(
            title="🎁 Hesabınız Başarıyla Üretildi!",
            description=f"İşte talep ettiğiniz `{kategori.upper()}` hesap bilgileri:\n\n`{secilen_hesap}`\n\n*Not: Hesabı güvenliğiniz için hemen değiştirmeniz önerilir.*",
            color=discord.Color.green()
        )
        await ctx.author.send(embed=dm_embed)
        
        # 2. Hesabı depodan siliyoruz (görünmez/kullanılmış kılıyoruz)
        bot.hesap_deposu[kategori].remove(secilen_hesap)
        
        # 3. Sunucuya herkesin göreceği başarı mesajını atıyoruz
        sunucu_embed = discord.Embed(
            title="🎉 BAŞARILI GENERATE!",
            description=f"{ctx.author.mention} az önce başarıyla bir **Real {kategori.upper()}** hesabı generateledi! 🚀",
            color=discord.Color.blue()
        )
        # Stokta kaç adet kaldığını da gösterelim
        kalan_stok = len(bot.hesap_deposu[kategori])
        sunucu_embed.set_footer(text=f"Kalan Güncel {kategori.upper()} Stoğu: {kalan_stok}")
        
        await ctx.send(embed=sunucu_embed)
        
    except discord.Forbidden:
        # Eğer kullanıcının DM'leri kapalıysa hata mesajı verir ve hesabı stoktan silmez
        await ctx.send(f"❌ {ctx.author.mention}, DM (Özel Mesaj) kutunuz kapalı olduğu için hesabı gönderemedim! Lütfen ayarlardan DM'leri açıp tekrar deneyin.")

TOKEN = os.getenv("DISCORD_TOKEN")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("HATA: 'DISCORD_TOKEN' bulunamadı.")
