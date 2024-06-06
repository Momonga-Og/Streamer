import discord
from discord.ext import commands
from discord import app_commands
import datetime
import json
import os

DATA_FILE = "activity_data.json"

class LoggingSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_counts = {}
        self.reaction_counts = {}
        self.voice_times = {}
        self.voice_state_cache = {}
        self.load_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.message_counts = data.get('message_counts', {})
                self.reaction_counts = data.get('reaction_counts', {})
                self.voice_times = data.get('voice_times', {})

    def save_data(self):
        data = {
            'message_counts': self.message_counts,
            'reaction_counts': self.reaction_counts,
            'voice_times': self.voice_times
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        user_id = str(message.author.id)
        self.message_counts[user_id] = self.message_counts.get(user_id, 0) + 1
        self.save_data()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        user_id = str(user.id)
        self.reaction_counts[user_id] = self.reaction_counts.get(user_id, 0) + 1
        self.save_data()

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if user.bot:
            return
        user_id = str(user.id)
        self.reaction_counts[user_id] = self.reaction_counts.get(user_id, 0) + 1
        self.save_data()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        user_id = str(member.id)
        if before.channel is None and after.channel is not None:
            # User joined a voice channel
            self.voice_state_cache[user_id] = datetime.datetime.now()
        elif before.channel is not None and after.channel is None:
            # User left a voice channel
            join_time = self.voice_state_cache.pop(user_id, None)
            if join_time:
                time_spent = (datetime.datetime.now() - join_time).total_seconds()
                self.voice_times[user_id] = self.voice_times.get(user_id, 0) + time_spent
                self.save_data()

    @app_commands.command(name="stats", description="Display overall server statistics")
    async def stats(self, interaction: discord.Interaction):
        top_users = sorted(self.message_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_channels = {}  # Implement if needed

        embed = discord.Embed(title="Server Statistics", color=discord.Color.blue())
        embed.add_field(
            name="Top Users by Messages",
            value="\n".join([f"<@{user_id}>: {count} messages" for user_id, count in top_users]),
            inline=False
        )
        # Add more fields as needed

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userstats", description="Display statistics for a specific user")
    @app_commands.describe(user="The user to display statistics for")
    async def userstats(self, interaction: discord.Interaction, user: discord.User):
        user_id = str(user.id)
        message_count = self.message_counts.get(user_id, 0)
        reaction_count = self.reaction_counts.get(user_id, 0)
        voice_time = self.voice_times.get(user_id, 0)

        embed = discord.Embed(title=f"Statistics for {user.display_name}", color=discord.Color.green())
        embed.add_field(name="Messages Sent", value=message_count, inline=False)
        embed.add_field(name="Reactions Added", value=reaction_count, inline=False)
        embed.add_field(name="Time in Voice (seconds)", value=voice_time, inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(LoggingSystem(bot))
