import discord
import os

class BotLogger:
    async def log(self, bot, guild: discord.Guild, action: str, details: str, color=discord.Color.blurple()):
        log_channel_id = int(os.getenv("LOG_CHANNEL_ID", 0))
        if not log_channel_id:
            return
        channel = guild.get_channel(log_channel_id)
        if not channel:
            return
        embed = discord.Embed(
            title=f"📋 {action}",
            description=details,
            color=color,
            timestamp=discord.utils.utcnow()
        )
        await channel.send(embed=embed)
