import discord
from discord.ext import commands
from discord import app_commands
import os

class Profiles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="View the top users by reputation")
    async def leaderboard(self, interaction: discord.Interaction):
        async with self.bot.db.db.execute(
            "SELECT user_id, reputation, vouches, deals_completed FROM users ORDER BY reputation DESC LIMIT 10"
        ) as c:
            rows = await c.fetchall()
        if not rows:
            return await interaction.response.send_message("No users registered yet.", ephemeral=True)
        embed = discord.Embed(title="🏆 Reputation Leaderboard", color=discord.Color.gold())
        for i, row in enumerate(rows, 1):
            user = interaction.guild.get_member(row[0])
            name = user.display_name if user else f"ID:{row[0]}"
            embed.add_field(
                name=f"#{i} {name}",
                value=f"⭐ {row[1]} rep | 🤝 {row[2]} vouches | ✅ {row[3]} deals",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="audit", description="[Staff] View recent audit log entries")
    async def audit(self, interaction: discord.Interaction):
        STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID", 0))
        if not any(r.id == STAFF_ROLE_ID for r in interaction.user.roles):
            return await interaction.response.send_message("❌ You don't have permission to do this.", ephemeral=True)
        async with self.bot.db.db.execute(
            "SELECT action, user_id, moderator_id, details, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 15"
        ) as c:
            rows = await c.fetchall()
        if not rows:
            return await interaction.response.send_message("No logs yet.", ephemeral=True)
        embed = discord.Embed(title="📋 Audit Logs", color=discord.Color.blurple())
        for row in rows:
            embed.add_field(
                name=f"{row[4]} — {row[0]}",
                value=f"User: <@{row[1]}> | Mod: <@{row[2]}>\n{row[3]}",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Profiles(bot))
