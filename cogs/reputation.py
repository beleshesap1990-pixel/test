import discord
from discord.ext import commands
from discord import app_commands

class DealConfirmView(discord.ui.View):
    def __init__(self, deal_id: int, buyer_id: int, seller_id: int):
        super().__init__(timeout=None)
        self.deal_id = deal_id
        self.buyer_id = buyer_id
        self.seller_id = seller_id

    @discord.ui.button(label="✅ Confirm Deal", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.buyer_id, self.seller_id):
            return await interaction.response.send_message("❌ You are not part of this deal.", ephemeral=True)
        role = "buyer" if interaction.user.id == self.buyer_id else "seller"
        await interaction.client.db.confirm_deal(self.deal_id, interaction.user.id, role)
        await interaction.response.send_message(f"✅ Your confirmation has been recorded ({role}).", ephemeral=True)

        async with interaction.client.db.db.execute(
            "SELECT buyer_confirmed, seller_confirmed FROM deals WHERE id=?", (self.deal_id,)
        ) as c:
            row = await c.fetchone()
        if row and row[0] and row[1]:
            await interaction.message.edit(
                content=f"🎉 **Deal #{self.deal_id} completed!** Both parties confirmed.",
                view=None
            )
            await interaction.client.db.add_reputation(self.buyer_id, 5)
            await interaction.client.db.add_reputation(self.seller_id, 5)
            await interaction.client.db.log_action("DEAL_COMPLETE", self.buyer_id, None,
                                                   f"Deal #{self.deal_id} completed. Buyer: {self.buyer_id}, Seller: {self.seller_id}")


class Reputation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="View a user's profile and reputation")
    @app_commands.describe(user="The user whose profile you want to view")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        await self.bot.db.ensure_user(target.id, str(target))
        row = await self.bot.db.get_user(target.id)
        vouches = await self.bot.db.get_vouches(target.id)

        embed = discord.Embed(title=f"👤 {target.display_name}", color=discord.Color.gold())
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="⭐ Reputation", value=str(row[2]))
        embed.add_field(name="🤝 Vouches", value=str(row[3]))
        embed.add_field(name="✅ Completed Deals", value=str(row[4]))

        if vouches:
            vouch_text = "\n".join([f"<@{v[0]}>: {v[1]}" for v in vouches[:3]])
            embed.add_field(name="💬 Recent Vouches", value=vouch_text, inline=False)

        embed.set_footer(text=f"Member since: {row[5]}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="vouch", description="Vouch for a user and boost their reputation")
    @app_commands.describe(user="The user you want to vouch for", comment="Leave a comment about them")
    async def vouch(self, interaction: discord.Interaction, user: discord.Member, comment: str):
        if user.id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot vouch for yourself.", ephemeral=True)
        await self.bot.db.ensure_user(user.id, str(user))
        await self.bot.db.ensure_user(interaction.user.id, str(interaction.user))
        await self.bot.db.add_vouch(interaction.user.id, user.id, comment)
        await self.bot.db.add_reputation(user.id, 10)
        embed = discord.Embed(
            description=f"✅ {interaction.user.mention} vouched for {user.mention}!\n💬 *{comment}*",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="deal", description="Start a deal with another user")
    @app_commands.describe(seller="The seller in this deal", description="What was agreed upon", amount="Deal amount")
    async def deal(self, interaction: discord.Interaction, seller: discord.Member, description: str, amount: str):
        if seller.id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot start a deal with yourself.", ephemeral=True)
        await self.bot.db.ensure_user(interaction.user.id, str(interaction.user))
        await self.bot.db.ensure_user(seller.id, str(seller))
        deal_id = await self.bot.db.create_deal(interaction.user.id, seller.id, description, amount)

        embed = discord.Embed(title=f"🤝 Deal #{deal_id}", color=discord.Color.orange())
        embed.add_field(name="Buyer", value=interaction.user.mention)
        embed.add_field(name="Seller", value=seller.mention)
        embed.add_field(name="Description", value=description, inline=False)
        embed.add_field(name="Amount", value=amount)
        embed.set_footer(text="Both parties must confirm to complete this deal!")

        view = DealConfirmView(deal_id, interaction.user.id, seller.id)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Reputation(bot))
