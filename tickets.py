import discord
from discord.ext import commands
from discord import app_commands, ui
import json
import os

class TicketView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @ui.button(label="الاستفسارات", style=discord.ButtonStyle.primary, custom_id="ticket_inquiries")
    async def ticket_inquiries(self, interaction: discord.Interaction, button: ui.Button):
        await self.create_ticket(interaction, "الاستفسارات")

    @ui.button(label="اقتراحات الديسكورد", style=discord.ButtonStyle.primary, custom_id="ticket_discord_suggestions")
    async def ticket_discord_suggestions(self, interaction: discord.Interaction, button: ui.Button):
        await self.create_ticket(interaction, "اقتراحات الديسكورد")

    @ui.button(label="شكاوي الديسكورد", style=discord.ButtonStyle.primary, custom_id="ticket_discord_complaints")
    async def ticket_discord_complaints(self, interaction: discord.Interaction, button: ui.Button):
        await self.create_ticket(interaction, "شكاوي الديسكورد")

    @ui.button(label="الادارة العليا", style=discord.ButtonStyle.primary, custom_id="ticket_admin")
    async def ticket_admin(self, interaction: discord.Interaction, button: ui.Button):
        await self.create_ticket(interaction, "الادارة العليا")

    @ui.button(label="العضويات", style=discord.ButtonStyle.primary, custom_id="ticket_memberships")
    async def ticket_memberships(self, interaction: discord.Interaction, button: ui.Button):
        await self.create_ticket(interaction, "العضويات")

    @ui.button(label="مشاكل الموقع", style=discord.ButtonStyle.primary, custom_id="ticket_website_issues")
    async def ticket_website_issues(self, interaction: discord.Interaction, button: ui.Button):
        await self.create_ticket(interaction, "مشاكل الموقع")

    @ui.button(label="اقتراحات الموقع", style=discord.ButtonStyle.primary, custom_id="ticket_website_suggestions")
    async def ticket_website_suggestions(self, interaction: discord.Interaction, button: ui.Button):
        await self.create_ticket(interaction, "اقتراحات الموقع")

    async def create_ticket(self, interaction: discord.Interaction, category: str):
        # Create a private channel
        guild = interaction.guild
        user = interaction.user
        category_name = f"{category}-{user.name}"

        # Check if the user already has an open ticket
        for channel in guild.channels:
            if channel.name == category_name:
                await interaction.response.send_message("You already have an open ticket.", ephemeral=True)
                return

        # Create the channel with specific permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            # Add any admin roles here with permissions
        }

        ticket_channel = await guild.create_text_channel(category_name, overwrites=overwrites)

        # Send a welcome message in the new channel
        await ticket_channel.send(f"Welcome {user.mention}! How can we help you with {category}?")

        # Notify admins about the new ticket
        admin_role = discord.utils.get(guild.roles, name="Admin")  # Change this to your admin role
        if admin_role:
            await ticket_channel.send(f"{admin_role.mention}, a new ticket has been created by {user.mention}.")

        await interaction.response.send_message(f"Your ticket has been created: {ticket_channel.mention}", ephemeral=True)


class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = {}

    @commands.command(name="setup_ticket_message")
    async def setup_ticket_message(self, ctx: commands.Context):
        embed = discord.Embed(title="الدعم الفني", description="مرحبًا! مِن هُنا يُمكنكَ فتح تذكرة للتواصل مع الدعم الفني...", color=discord.Color.blue())
        await ctx.send(embed=embed, view=TicketView(self.bot))

    @app_commands.command(name="config_ticket", description="Configure the ticket system")
    async def config_ticket(self, interaction: discord.Interaction):
        await interaction.response.send_message("Configure the ticket system here.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
