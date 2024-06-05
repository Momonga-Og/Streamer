import discord
from discord.ext import commands
import json
import os
import welcome
import pin_settings

intents = discord.Intents.default()
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Load configuration
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()  # Sync the command tree with Discord

# Import functionalities
welcome.setup(bot, config)
pin_settings.setup(bot, config)

bot.run(config['bot_token'])
