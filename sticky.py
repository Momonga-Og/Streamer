import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os

class StickyMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stickies = {}
        self.load_stickies()

    def load_stickies(self):
        if os.path.exists('stickies.json'):
            with open('stickies.json', 'r', encoding='utf-8') as f:
                self.stickies = json.load(f)

    def save_stickies(self):
        with open('stickies.json', 'w', encoding='utf-8') as f:
            json.dump(self.stickies, f, ensure_ascii=False, indent=4)

    @app_commands.command(name="stick", description="Stick a message to the channel")
    @app_commands.describe(message="The message to stick")
    async def stick(self, interaction: discord.Interaction, message: str):
        """Sticks your message to the channel."""
        channel_id = str(interaction.channel.id)
        if channel_id in self.stickies:
            self.stickies[channel_id]["message"] = message
            self.stickies[channel_id]["active"] = True
        else:
            self.stickies[channel_id] = {"message": message, "active": True, "message_id": None}

        self.save_stickies()
        await interaction.response.send_message(f"Sticky message set: {message}")

        await self.post_sticky(interaction.channel)

    @app_commands.command(name="stickstop", description="Stop the current sticky message in the channel")
    async def stickstop(self, interaction: discord.Interaction):
        """Stops the current sticky in the channel."""
        channel_id = str(interaction.channel.id)
        if channel_id in self.stickies and self.stickies[channel_id]["active"]:
            self.stickies[channel_id]["active"] = False
            self.save_stickies()
            await interaction.response.send_message("Sticky message stopped.")
        else:
            await interaction.response.send_message("No active sticky message in this channel.")

    @app_commands.command(name="stickstart", description="Restart a stopped sticky message in the channel")
    async def stickstart(self, interaction: discord.Interaction):
        """Restarts a stopped sticky message using the previous message."""
        channel_id = str(interaction.channel.id)
        if channel_id in self.stickies and not self.stickies[channel_id]["active"]:
            self.stickies[channel_id]["active"] = True
            self.save_stickies()
            await interaction.response.send_message("Sticky message restarted.")
            await self.post_sticky(interaction.channel)
        else:
            await interaction.response.send_message("No stopped sticky message to restart in this channel.")

    @app_commands.command(name="stickremove", description="Remove the sticky message in the channel")
    async def stickremove(self, interaction: discord.Interaction):
        """Stops and completely deletes the sticky message in this channel."""
        channel_id = str(interaction.channel.id)
        if channel_id in self.stickies:
            del self.stickies[channel_id]
            self.save_stickies()
            await interaction.response.send_message("Sticky message removed.")
        else:
            await interaction.response.send_message("No sticky message to remove in this channel.")

    @app_commands.command(name="getstickies", description="Get all active stickies in the server")
    async def getstickies(self, interaction: discord.Interaction):
        """Gets all active stickies in the server."""
        active_stickies = [f"<#{channel_id}>: {info['message']}" for channel_id, info in self.stickies.items() if info["active"]]
        if active_stickies:
            await interaction.response.send_message("Active stickies:\n" + "\n".join(active_stickies))
        else:
            await interaction.response.send_message("No active stickies in the server.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        channel_id = str(message.channel.id)
        if channel_id in self.stickies and self.stickies[channel_id]["active"]:
            await self.post_sticky(message.channel)

    async def post_sticky(self, channel):
        sticky_info = self.stickies.get(str(channel.id))
        if sticky_info and sticky_info["active"]:
            # Delete previous sticky message if it exists
            if sticky_info["message_id"]:
                try:
                    prev_message = await channel.fetch_message(sticky_info["message_id"])
                    await prev_message.delete()
                except discord.NotFound:
                    pass

            # Send new sticky message
            sent_message = await channel.send(sticky_info["message"])
            sticky_info["message_id"] = sent_message.id
            self.save_stickies()

async def setup(bot):
    await bot.add_cog(StickyMessages(bot))
