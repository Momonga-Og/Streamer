import discord
from discord.ext import commands
from discord import app_commands
import requests
from bs4 import BeautifulSoup
import os

# Load token from environment variable
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Server IDs mapping
servers = {
    'dodge': 406,
    'grandapan': 403,
    'herdegrize': 404,
    'terra-cogita': 405,
    # Add other servers if needed
}

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Bot is ready. Logged in as {bot.user}')

def fetch_character_info(name, server, level_min, level_max):
    server_id = servers.get(server.lower())
    if not server_id:
        return None, f"Server '{server}' not found."

    url = (
        f"https://www.dofus-touch.com/en/mmorpg/community/directories/character-pages"
        f"?text={name}&character_homeserv%5B%5D={server_id}"
        f"&character_level_min={level_min}&character_level_max={level_max}#jt_list"
    )
    print(f"Fetching URL: {url}")  # Log the URL for debugging

    response = requests.get(url)
    print(f"HTTP Response Status Code: {response.status_code}")  # Log the status code

    if response.status_code != 200:
        return None, "Failed to fetch data from the website."

    soup = BeautifulSoup(response.text, 'html.parser')
    first_result = soup.find('div', class_='ak-character-info')  # Adjust based on actual HTML structure
    if not first_result:
        return None, "No results found."

    first_result_link = first_result.find('a')['href']
    first_result_url = f"https://www.dofus-touch.com{first_result_link}"
    
    # Extracting additional details for embedding
    character_name = first_result.find('div', class_='ak-name').text.strip()
    character_level = first_result.find('div', class_='ak-level').text.strip()
    character_class = first_result.find('div', class_='ak-class').text.strip()
    
    character_info = {
        'url': first_result_url,
        'name': character_name,
        'level': character_level,
        'class': character_class
    }
    
    return character_info, None

@bot.tree.command(name='search', description='Search for a character')
async def search(interaction: discord.Interaction, name: str, server: str, level_min: int, level_max: int):
    result, error = fetch_character_info(name, server, level_min, level_max)
    if error:
        await interaction.response.send_message(error)
    else:
        embed = discord.Embed(
            title=result['name'],
            url=result['url'],
            description=f"Class: {result['class']}\nLevel: {result['level']}",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
