import discord
from discord.ext import commands
from discord import app_commands
import os

STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID", 0))
REPORT_CHANNEL_ID = int(os.getenv("REPORT_CHANNEL_ID", 0))

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_staff(self, member: discord.Member) -> bool:
        return any(r.id == STAFF_ROLE_ID for r in member.roles)

    @app_commands.command(name="report", description="Bir kullanıcıyı raporla")
    @app_commands.describe(user="Raporlamak istediğin kişi", reason="Sebep", evidence="Kanıt (link, ekran görüntüsü vb.)")
    async def report(self, interaction: discord.Interaction, user: discord.Member, reason: str, evidence: str = "Yok"):
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ Kendini raporlayamazsın.", ephemeral=True)
        report_id = await self.bot.db.create_report(interaction.user.id, user.id, reason, evidence)

        if REPORT_CHANNEL_ID:
            ch = interaction.guild.get_channel(REPORT_CHANNEL_ID)
            if ch:
                embed = discord.Embed(
                    title=f"🚨 Yeni Rapor #{report_id}",
                    color=discord.Color.red()
                )
                embed.add_field(name="Raporlayan", value=interaction.user.mention)
                embed.add_field(name="Raporlanan", value=user.mention)
                embed.add_field(name="Sebep", value=reason, inline=False)
                embed.add_field(name="Kanıt", value=evidence, inline=False)
                await ch.send(embed=embed)

        await interaction.response.send_message(f"✅ Rapor #{report_id} alındı. Staff inceleyecek.", ephemeral=True)

    @app_commands.command(name="warn", description="[Staff] Kullanıcıya uyarı ver")
    @app_commands.describe(user="Uyarılacak kişi", reason="Sebep")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if not self.is_staff(interaction.user):
            return await interaction.response.send_message("❌ Yetkin yok.", ephemeral=True)
        await self.bot.db.log_action("WARN", user.id, interaction.user.id, reason)
        try:
            await user.send(f"⚠️ **{interaction.guild.name}** sunucusunda uyarı aldın!\nSebep: {reason}")
        except discord.Forbidden:
            pass
        embed = discord.Embed(description=f"⚠️ {user.mention} uyarıldı. Sebep: {reason}", color=discord.Color.yellow())
        await interaction.response.send_message(embed=embed)
        await self.bot.bot_logger.log(self.bot, interaction.guild, "UYARI", f"{user} uyarıldı: {reason}", discord.Color.yellow())

    @app_commands.command(name="kick", description="[Staff] Kullanıcıyı kickle")
    @app_commands.describe(user="Kicklenecek kişi", reason="Sebep")
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Belirtilmedi"):
        if not self.is_staff(interaction.user):
            return await interaction.response.send_message("❌ Yetkin yok.", ephemeral=True)
        await user.kick(reason=reason)
        await self.bot.db.log_action("KICK", user.id, interaction.user.id, reason)
        await interaction.response.send_message(f"👢 {user.mention} kicklendi. Sebep: {reason}")
        await self.bot.bot_logger.log(self.bot, interaction.guild, "KICK", f"{user} kicklendi: {reason}", discord.Color.orange())

    @app_commands.command(name="ban", description="[Staff] Kullanıcıyı banla")
    @app_commands.describe(user="Banlanacak kişi", reason="Sebep")
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Belirtilmedi"):
        if not self.is_staff(interaction.user):
            return await interaction.response.send_message("❌ Yetkin yok.", ephemeral=True)
        await user.ban(reason=reason)
        await self.bot.db.log_action("BAN", user.id, interaction.user.id, reason)
        await interaction.response.send_message(f"🔨 {user.mention} banlandı. Sebep: {reason}")
        await self.bot.bot_logger.log(self.bot, interaction.guild, "BAN", f"{user} banlandı: {reason}", discord.Color.red())

    @app_commands.command(name="timeout", description="[Staff] Kullanıcıya timeout ver")
    @app_commands.describe(user="Timeout verilecek kişi", minutes="Dakika", reason="Sebep")
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, minutes: int, reason: str = "Belirtilmedi"):
        if not self.is_staff(interaction.user):
            return await interaction.response.send_message("❌ Yetkin yok.", ephemeral=True)
        import datetime
        duration = datetime.timedelta(minutes=minutes)
        await user.timeout(duration, reason=reason)
        await self.bot.db.log_action("TIMEOUT", user.id, interaction.user.id, f"{minutes}dk - {reason}")
        await interaction.response.send_message(f"⏱️ {user.mention} {minutes} dakika timeout aldı. Sebep: {reason}")
        await self.bot.bot_logger.log(self.bot, interaction.guild, "TIMEOUT", f"{user} {minutes}dk timeout: {reason}", discord.Color.orange())


async def setup(bot):
    await bot.add_cog(Moderation(bot))
