import discord
from discord.ext import commands
from discord import app_commands, ui
import datetime
import json
import os
import random

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
        guild = interaction.guild
        user = interaction.user
        channel_name = f"ticket-{category}-{user.name}".replace(" ", "-")

        # Check if the user already has an open ticket
        for channel in guild.channels:
            if channel.name == channel_name:
                await interaction.response.send_message("You already have an open ticket.", ephemeral=True)
                return

        # Create the channel with specific permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            discord.utils.get(guild.roles, name="Admin"): discord.PermissionOverwrite(read_messages=True)
        }

        ticket_channel = await guild.create_text_channel(channel_name, overwrites=overwrites)

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
        self.transcripts_path = "transcripts"  # Folder to store ticket transcripts

    @app_commands.command(name="panel", description="Create a new ticket panel")
    async def panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="الدعم الفني",
            description="مرحبًا! مِن هُنا يُمكنكَ فتح تذكرة للتواصل مع الدعم الفني...\n\n"
                        "︶ ︶︶︶ ︶︶︶ ︶︶︶\n"
                        "تحذير ، أي تذكرة تم فتحها بدون سبب سيتم مُعاقبه صاحبها\n"
                        "︶ ︶︶︶ ︶︶︶ ︶︶︶\n"
                        "قسم الشكاوي العامة\n"
                        "╭ㅤ୨ 🤔 ꒱﹒إذا كان لديك استفسار عن شيءٍ ما\n"
                        "┊ㅤ୨ 🧞 ꒱﹒ لاقتراحات الديسكورد\n"
                        "┊ㅤ୨ 🛠️ ꒱﹒إذا واجهتك مشكلة في سيرفر الديسكورد (الإعتراض علي ميوت - علي باند - مشاكل مع عضو مشكلة في بوت)\n"
                        "╰ㅤ୨ ⚡ ꒱﹒إذا واجهتك مشكلة تطلب الإدارة العُليا - تريد من أحد مراجعة تقديمك - الاستفسارات بخصوص التقديم و آليه عمل الموقع والربح\n"
                        "قسم الموقع\n"
                        "╭ㅤ୨ 🤔 ꒱﹒استفسارات العضويات (شراء-تفعيل العضوية)\n"
                        "┊ㅤ୨ 🌐 ꒱﹒إذا واجهتك مشكلة في الموقع (حسابك لا يعمل - الموقع لا يعمل - الخ)\n"
                        "╰ㅤ୨ 💡 ꒱﹒للإدلاء باقتراح خطر ببالك لتطوير الموقع\n"
                        "- مُلاحظة - يُرجى التحلي بالصبر عند فتح التذكرة!\n"
                        "لا يتم التسامح مع المخربين أو غير المُحترمين!",
            color=discord.Color.blue()
        )
        await interaction.channel.send(embed=embed, view=TicketView(self.bot))
        await interaction.response.send_message("Ticket panel created.", ephemeral=True)

    @app_commands.command(name="close", description="Close an active ticket")
    async def close(self, interaction: discord.Interaction):
        if not interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message("This command can only be used in a ticket channel.", ephemeral=True)
            return

        user = interaction.user
        transcript = []
        async for message in interaction.channel.history(limit=None, oldest_first=True):
            timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
            transcript.append(f"[{timestamp}] {message.author.display_name}: {message.content}")

        transcript_path = os.path.join(self.transcripts_path, f"{interaction.channel.name}.txt")
        os.makedirs(self.transcripts_path, exist_ok=True)
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(transcript))

        await interaction.channel.send(f"The ticket has been closed by {user.mention}. Transcript saved.")
        await interaction.response.send_message(f"Ticket closed and transcript saved: {transcript_path}", ephemeral=True)
        await interaction.channel.delete()

    @app_commands.command(name="ticket", description="Displays information and options for in-ticket management")
    async def ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Ticket Management", description="Options for managing this ticket.", color=discord.Color.green())
        embed.add_field(name="/claim", value="Claim the current ticket.", inline=False)
        embed.add_field(name="/lock", value="Lock the ticket and disallow the user to view the channel.", inline=False)
        embed.add_field(name="/unlock", value="Unlock the ticket and allow the user to view the channel.", inline=False)
        embed.add_field(name="/close", value="Close the ticket and save the transcript.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="claim", description="Claim the current ticket")
    async def claim(self, interaction: discord.Interaction):
        if not interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message("This command can only be used in a ticket channel.", ephemeral=True)
            return

        await interaction.channel.send(f"{interaction.user.mention} has claimed this ticket.")
        await interaction.response.send_message("You have claimed this ticket.", ephemeral=True)

    @app_commands.command(name="lock", description="Lock the ticket and disallow the user to view the channel")
    async def lock(self, interaction: discord.Interaction):
        if not interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message("This command can only be used in a ticket channel.", ephemeral=True)
            return

        user = interaction.channel.overwrites_for(interaction.user)
        user.read_messages = False
        await interaction.channel.set_permissions(interaction.user, overwrite=user)
        await interaction.channel.send(f"{interaction.user.mention} has locked the ticket.")
        await interaction.response.send_message("You have locked this ticket.", ephemeral=True)

    @app_commands.command(name="unlock", description="Unlock the ticket and allow the user to view the channel")
    async def unlock(self, interaction: discord.Interaction):
        if not interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message("This command can only be used in a ticket channel.", ephemeral=True)
            return

        user = interaction.channel.overwrites_for(interaction.user)
        user.read_messages = True
        await interaction.channel.set_permissions(interaction.user, overwrite=user)
        await interaction.channel.send(f"{interaction.user.mention} has unlocked the ticket.")
        await interaction.response.send_message("You have unlocked this ticket.", ephemeral=True)

    @app_commands.command(name="config", description="Configure the ticket system")
    async def config(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Ticket System Configuration", description="Configure the ticket system here.", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
