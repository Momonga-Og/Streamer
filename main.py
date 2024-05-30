import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os

# Discord bot token
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# URL of the Al Jazeera live stream
LIVE_STREAM_URL = 'https://www.youtube.com/live/mJdhDuweBHM?si=c_5TTVceID7Raq2i'

# Define a custom Bot class that extends commands.Bot
class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        await self.tree.sync()

# Intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize the bot
bot = MyBot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(f'Invite the bot using: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands')

@bot.tree.command(name='eljazeera', description='Show the Al Jazeera live stream')
async def eljazeera(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'force_generic_extractor': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(LIVE_STREAM_URL, download=False)
            stream_url = info['url']

        await interaction.followup.send(f'Al Jazeera Live Stream: {stream_url}')
    except Exception as e:
        await interaction.followup.send(f'Failed to fetch live stream: {str(e)}')

# Run the bot
bot.run(DISCORD_BOT_TOKEN)
