import discord
from discord.ext import commands
import os

LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, guild, embed):
        if not LOG_CHANNEL_ID:
            return
        ch = guild.get_channel(LOG_CHANNEL_ID)
        if ch:
            await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.bot.db.ensure_user(member.id, str(member))
        embed = discord.Embed(
            title="📥 Üye Katıldı",
            description=f"{member.mention} sunucuya katıldı.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Hesap Oluşturma", value=discord.utils.format_dt(member.created_at, "R"))
        embed.set_footer(text=f"ID: {member.id}")
        await self.send_log(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        embed = discord.Embed(
            title="📤 Üye Ayrıldı",
            description=f"{member} sunucudan ayrıldı.",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"ID: {member.id}")
        await self.send_log(member.guild, embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        embed = discord.Embed(
            title="🗑️ Mesaj Silindi",
            description=f"**Kanal:** {message.channel.mention}\n**Kullanıcı:** {message.author.mention}\n**İçerik:** {message.content[:500] or '*[Görüntülenemiyor]*'}",
            color=discord.Color.dark_red()
        )
        embed.set_footer(text=f"Mesaj ID: {message.id}")
        await self.send_log(message.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild or before.content == after.content:
            return
        embed = discord.Embed(
            title="✏️ Mesaj Düzenlendi",
            description=f"**Kanal:** {before.channel.mention}\n**Kullanıcı:** {before.author.mention}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Öncesi", value=before.content[:400] or "*boş*", inline=False)
        embed.add_field(name="Sonrası", value=after.content[:400] or "*boş*", inline=False)
        embed.set_footer(text=f"Mesaj ID: {before.id}")
        await self.send_log(before.guild, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]
            if not added and not removed:
                return
            embed = discord.Embed(title="🎭 Rol Değişikliği", color=discord.Color.purple())
            embed.add_field(name="Kullanıcı", value=after.mention)
            if added:
                embed.add_field(name="Eklenen", value=", ".join(r.mention for r in added))
            if removed:
                embed.add_field(name="Kaldırılan", value=", ".join(r.mention for r in removed))
            await self.send_log(after.guild, embed)


async def setup(bot):
    await bot.add_cog(Logging(bot))
