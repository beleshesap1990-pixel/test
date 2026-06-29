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

    @app_commands.command(name="report", description="Report a user to the staff team")
    @app_commands.describe(user="The user you want to report", reason="Reason for the report", evidence="Evidence (links, screenshots, etc.)")
    async def report(self, interaction: discord.Interaction, user: discord.Member, reason: str, evidence: str = "None provided"):
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot report yourself.", ephemeral=True)
        report_id = await self.bot.db.create_report(interaction.user.id, user.id, reason, evidence)

        if REPORT_CHANNEL_ID:
            ch = interaction.guild.get_channel(REPORT_CHANNEL_ID)
            if ch:
                embed = discord.Embed(title=f"🚨 New Report #{report_id}", color=discord.Color.red())
                embed.add_field(name="Reporter", value=interaction.user.mention)
                embed.add_field(name="Reported User", value=user.mention)
                embed.add_field(name="Reason", value=reason, inline=False)
                embed.add_field(name="Evidence", value=evidence, inline=False)
                await ch.send(embed=embed)

        await interaction.response.send_message(f"✅ Report #{report_id} submitted. Staff will review it shortly.", ephemeral=True)

    @app_commands.command(name="warn", description="[Staff] Warn a user")
    @app_commands.describe(user="The user to warn", reason="Reason for the warning")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if not self.is_staff(interaction.user):
            return await interaction.response.send_message("❌ You don't have permission to do this.", ephemeral=True)
        await self.bot.db.log_action("WARN", user.id, interaction.user.id, reason)
        try:
            await user.send(f"⚠️ You have been warned in **{interaction.guild.name}**.\nReason: {reason}")
        except discord.Forbidden:
            pass
        embed = discord.Embed(description=f"⚠️ {user.mention} has been warned. Reason: {reason}", color=discord.Color.yellow())
        await interaction.response.send_message(embed=embed)
        await self.bot.bot_logger.log(self.bot, interaction.guild, "WARN", f"{user} was warned: {reason}", discord.Color.yellow())

    @app_commands.command(name="kick", description="[Staff] Kick a user from the server")
    @app_commands.describe(user="The user to kick", reason="Reason for the kick")
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        if not self.is_staff(interaction.user):
            return await interaction.response.send_message("❌ You don't have permission to do this.", ephemeral=True)
        await user.kick(reason=reason)
        await self.bot.db.log_action("KICK", user.id, interaction.user.id, reason)
        await interaction.response.send_message(f"👢 {user.mention} has been kicked. Reason: {reason}")
        await self.bot.bot_logger.log(self.bot, interaction.guild, "KICK", f"{user} was kicked: {reason}", discord.Color.orange())

    @app_commands.command(name="ban", description="[Staff] Ban a user from the server")
    @app_commands.describe(user="The user to ban", reason="Reason for the ban")
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        if not self.is_staff(interaction.user):
            return await interaction.response.send_message("❌ You don't have permission to do this.", ephemeral=True)
        await user.ban(reason=reason)
        await self.bot.db.log_action("BAN", user.id, interaction.user.id, reason)
        await interaction.response.send_message(f"🔨 {user.mention} has been banned. Reason: {reason}")
        await self.bot.bot_logger.log(self.bot, interaction.guild, "BAN", f"{user} was banned: {reason}", discord.Color.red())

    @app_commands.command(name="timeout", description="[Staff] Timeout a user")
    @app_commands.describe(user="The user to timeout", minutes="Duration in minutes", reason="Reason for the timeout")
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, minutes: int, reason: str = "No reason provided"):
        if not self.is_staff(interaction.user):
            return await interaction.response.send_message("❌ You don't have permission to do this.", ephemeral=True)
        import datetime
        duration = datetime.timedelta(minutes=minutes)
        await user.timeout(duration, reason=reason)
        await self.bot.db.log_action("TIMEOUT", user.id, interaction.user.id, f"{minutes}min - {reason}")
        await interaction.response.send_message(f"⏱️ {user.mention} has been timed out for {minutes} minutes. Reason: {reason}")
        await self.bot.bot_logger.log(self.bot, interaction.guild, "TIMEOUT", f"{user} timed out {minutes}min: {reason}", discord.Color.orange())


async def setup(bot):
    await bot.add_cog(Moderation(bot))
