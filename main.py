import discord
from discord.ext import commands
from discord import app_commands
import os

# Discord bot token
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Define a custom Bot class that extends commands.Bot
class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.voice_client = None

    async def setup_hook(self):
        # Synchronize the application commands with the Discord API
        await bot.tree.sync()

# Intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize the bot
bot = MyBot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(f'Invite the bot using: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands')

@bot.tree.command(name='join', description='Join a voice channel')
async def join_channel(interaction: discord.Interaction):
    channel = interaction.user.voice.channel
    bot.voice_client = await channel.connect()
    await interaction.response.send_message("Joined the voice channel.")

@bot.tree.command(name='leave', description='Leave the current voice channel')
async def leave_channel(interaction: discord.Interaction):
    if bot.voice_client:
        await bot.voice_client.disconnect()
        bot.voice_client = None
        await interaction.response.send_message("Left the voice channel.")
    else:
        await interaction.response.send_message("Bot is not connected to a voice channel.")

@bot.tree.command(name='play', description='Play a stream in the current voice channel')
async def play_stream(interaction: discord.Interaction, stream_url: str):
    if bot.voice_client is None or not bot.voice_client.is_connected():
        await interaction.response.send_message("Bot is not connected to a voice channel. Use /join to connect.")
        return

    try:
        source = discord.FFmpegPCMAudio(stream_url)
        bot.voice_client.play(source)
        await interaction.response.send_message("Playing stream.")
    except Exception as e:
        await interaction.response.send_message(f"Failed to play stream: {e}")

@bot.tree.command(name='stop', description='Stop playing the stream')
async def stop_stream(interaction: discord.Interaction):
    if bot.voice_client and bot.voice_client.is_playing():
        bot.voice_client.stop()
        await interaction.response.send_message("Stream stopped.")
    else:
        await interaction.response.send_message("No stream is currently playing.")

# Run the bot
bot.run(DISCORD_BOT_TOKEN)
