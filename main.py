import discord
from discord.ext import commands
import yt_dlp
import os

# Discord bot token
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# URL of the Al Jazeera live stream
LIVE_STREAM_URL = 'https://www.youtube.com/live/mJdhDuweBHM?si=c_5TTVceID7Raq2i'

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.slash_command(name='eljazeera', description='Show the Al Jazeera live stream')
async def eljazeera(ctx):
    await ctx.defer()
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
        
        await ctx.send(f'Al Jazeera Live Stream: {stream_url}')
    except Exception as e:
        await ctx.send(f'Failed to fetch live stream: {str(e)}')

bot.run(DISCORD_BOT_TOKEN)
