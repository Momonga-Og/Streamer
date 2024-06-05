import discord
from discord.ext import commands
import json
from discord import File
import os

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Load configuration
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_member_join(member):
    # Debugging statement
    print(f'Member joined: {member.name}')
    
    # Look for the welcome channel
    channel = discord.utils.get(member.guild.text_channels, name='welcome')
    
    if channel:
        print(f'Found welcome channel: {channel.name}')
        
        try:
            # Open the welcome image
            with open(config['welcome_image'], 'rb') as f:
                picture = File(f)

                # Build the welcome message
                message = f"{config['welcome_message']}\n╰ ╮・ ┈ ┈ ┈ ┈ ┈ ┈ ┈ ┈ ↓ ↓\n"
                message += "╭ ╯ㅤ@𝖈𝖍𝖆𝖔𝖘\n— — — — —  — — — —\n"
                for ch in config['channels']:
                    message += f"📖 ⨯ ・{ch['description']} ⁠«{ch['channel']}»\n"
                message += "— — — — —  — — — —\n"
                message += f"⊹ ˚. 🌟┊⢀ ₊ ˚ ღ ˚. 🌍 ┊・ ˚.\n˚. ┊・ ⊹ ₊ ˚{config['footer']} ღ ˚. 🌠 ┊・"

                await channel.send(message, file=picture)
                print('Welcome message sent.')
        except KeyError as e:
            print(f'Error: Missing key {e} in config.json')
        except FileNotFoundError:
            print('Error: Welcome image file not found.')
    else:
        print('Welcome channel not found.')

# Run the bot with your token from the configuration file
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
