import discord
from discord.ext import commands
from discord import app_commands

class Profiles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="En yüksek reputasyonlu kullanıcılar")
    async def leaderboard(self, interaction: discord.Interaction):
        async with self.bot.db.db.execute(
            "SELECT user_id, reputation, vouches, deals_completed FROM users ORDER BY reputation DESC LIMIT 10"
        ) as c:
            rows = await c.fetchall()
        if not rows:
            return await interaction.response.send_message("Henüz kayıtlı kullanıcı yok.", ephemeral=True)
        embed = discord.Embed(title="🏆 Reputation Sıralaması", color=discord.Color.gold())
        for i, row in enumerate(rows, 1):
            user = interaction.guild.get_member(row[0])
            name = user.display_name if user else f"ID:{row[0]}"
            embed.add_field(
                name=f"#{i} {name}",
                value=f"⭐ {row[1]} rep | 🤝 {row[2]} vouch | ✅ {row[3]} deal",
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="audit", description="[Staff] Son audit loglarını gör")
    async def audit(self, interaction: discord.Interaction):
        from utils.logger import BotLogger
        import os
        STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID", 0))
        if not any(r.id == STAFF_ROLE_ID for r in interaction.user.roles):
            return await interaction.response.send_message("❌ Yetkin yok.", ephemeral=True)
        async with self.bot.db.db.execute(
            "SELECT action, user_id, moderator_id, details, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 15"
        ) as c:
            rows = await c.fetchall()
        if not rows:
            return await interaction.response.send_message("Henüz log yok.", ephemeral=True)
        embed = discord.Embed(title="📋 Audit Logları", color=discord.Color.blurple())
        for row in rows:
            embed.add_field(
                name=f"{row[4]} — {row[0]}",
                value=f"Kullanıcı: <@{row[1]}> | Mod: <@{row[2]}>\n{row[3]}",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Profiles(bot))
