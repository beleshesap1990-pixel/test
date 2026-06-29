import discord
from discord.ext import commands
from discord import app_commands
import os

STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID", 0))
APPROVED_CHANNEL_ID = int(os.getenv("APPROVED_CHANNEL_ID", 0))
QUEUE_CHANNEL_ID = int(os.getenv("QUEUE_CHANNEL_ID", 0))

class ApprovalView(discord.ui.View):
    def __init__(self, post_id: int):
        super().__init__(timeout=None)
        self.post_id = post_id

    @discord.ui.button(label="✅ Onayla", style=discord.ButtonStyle.success, custom_id="approve_post")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(r.id == STAFF_ROLE_ID for r in interaction.user.roles):
            return await interaction.response.send_message("❌ Yetkin yok.", ephemeral=True)
        await interaction.client.db.approve_post(self.post_id, interaction.user.id)
        await interaction.client.db.log_action("POST_APPROVED", None, interaction.user.id, f"Post #{self.post_id} onaylandı")
        await interaction.message.edit(content="✅ **Onaylandı**", view=None)
        await interaction.response.send_message("Post onaylandı!", ephemeral=True)

        # Onaylanan postu yayınla
        row = await interaction.client.db.db.execute("SELECT * FROM hiring_posts WHERE id=?", (self.post_id,))
        post = await row.fetchone()
        if post and APPROVED_CHANNEL_ID:
            ch = interaction.guild.get_channel(APPROVED_CHANNEL_ID)
            if ch:
                embed = build_post_embed(post, interaction.guild)
                await ch.send(embed=embed)

    @discord.ui.button(label="❌ Reddet", style=discord.ButtonStyle.danger, custom_id="reject_post")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(r.id == STAFF_ROLE_ID for r in interaction.user.roles):
            return await interaction.response.send_message("❌ Yetkin yok.", ephemeral=True)
        await interaction.client.db.reject_post(self.post_id, interaction.user.id)
        await interaction.message.edit(content="❌ **Reddedildi**", view=None)
        await interaction.response.send_message("Post reddedildi.", ephemeral=True)


def build_post_embed(post, guild):
    user = guild.get_member(post[1])
    type_label = "🧑‍💼 Hiring" if post[2] == "hiring" else "💼 For Hire"
    embed = discord.Embed(
        title=f"{type_label} — {post[3]}",
        description=post[4],
        color=discord.Color.green() if post[2] == "hiring" else discord.Color.blue()
    )
    embed.add_field(name="💰 Bütçe/Ücret", value=post[5])
    embed.set_footer(text=f"Post #{post[0]} | {user.display_name if user else post[1]}")
    return embed


class HiringModal(discord.ui.Modal):
    def __init__(self, post_type: str):
        super().__init__(title="Hiring Post" if post_type == "hiring" else "For Hire Post")
        self.post_type = post_type
        self.title_input = discord.ui.TextInput(label="Başlık", max_length=100)
        self.description = discord.ui.TextInput(label="Açıklama", style=discord.TextStyle.paragraph, max_length=1000)
        self.budget = discord.ui.TextInput(label="Bütçe / Beklenen Ücret", max_length=50)
        self.add_item(self.title_input)
        self.add_item(self.description)
        self.add_item(self.budget)

    async def on_submit(self, interaction: discord.Interaction):
        db = interaction.client.db
        await db.ensure_user(interaction.user.id, str(interaction.user))
        post_id = await db.create_hiring_post(
            interaction.user.id,
            self.post_type,
            self.title_input.value,
            self.description.value,
            self.budget.value
        )
        # Staff kuyruğuna gönder
        if QUEUE_CHANNEL_ID:
            ch = interaction.guild.get_channel(QUEUE_CHANNEL_ID)
            if ch:
                embed = discord.Embed(
                    title=f"📥 Yeni {'Hiring' if self.post_type == 'hiring' else 'For Hire'} Post — #{post_id}",
                    description=f"**Başlık:** {self.title_input.value}\n**Açıklama:** {self.description.value}\n**Bütçe:** {self.budget.value}",
                    color=discord.Color.orange()
                )
                embed.set_footer(text=f"Kullanıcı: {interaction.user} ({interaction.user.id})")
                await ch.send(embed=embed, view=ApprovalView(post_id))

        await interaction.response.send_message(
            f"✅ Postun alındı (#{post_id}). Staff onayından sonra yayınlanacak.", ephemeral=True
        )


class Hiring(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="hiring", description="Birini işe almak için post aç")
    async def hiring(self, interaction: discord.Interaction):
        await interaction.response.send_modal(HiringModal("hiring"))

    @app_commands.command(name="for-hire", description="Hizmet sunmak için post aç")
    async def for_hire(self, interaction: discord.Interaction):
        await interaction.response.send_modal(HiringModal("for_hire"))

    @app_commands.command(name="queue", description="[Staff] Bekleyen postları listele")
    async def queue(self, interaction: discord.Interaction):
        if not any(r.id == STAFF_ROLE_ID for r in interaction.user.roles):
            return await interaction.response.send_message("❌ Yetkin yok.", ephemeral=True)
        posts = await self.bot.db.get_pending_posts()
        if not posts:
            return await interaction.response.send_message("✅ Bekleyen post yok.", ephemeral=True)
        text = "\n".join([f"#{p[0]} | {p[2]} | {p[3]} | <@{p[1]}>" for p in posts])
        await interaction.response.send_message(f"**Bekleyen Postlar:**\n{text}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Hiring(bot))
