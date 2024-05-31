import os
import json
import requests
from bs4 import BeautifulSoup
from discord.ext import commands
from discord import Intents, Embed, app_commands

import discord

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Load configuration and sentences
with open('config.json') as f:
    settings = json.load(f)

with open('language.json') as f:
    sentences = json.load(f)

# Constants
VERSION = os.getenv("API_VERSION", "1.49.5")

# Initialize the bot
intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'We have logged in as {bot.user}')

@bot.tree.command(name="whois")
async def whois(interaction: discord.Interaction, pseudo: str, level: int = None, server: str = "406"):
    await interaction.response.defer()
    pseudo = pseudo.lower()
    lang_map = {'fr': 0, 'en': 1}
    config = {'lang': 'en'}  # Default language is set to English
    lang_index = lang_map.get(config['lang'], 1)  # Default to English if language not found

    base_url = f"{settings['encyclopedia']['base_url']}/{settings['encyclopedia']['player_url'][lang_index]}"
    try:
        print(f"Using base URL: {base_url}")
        print(f"Parameters - Pseudo: {pseudo}, Server: {server}, Level: {level}")
        
        player_url = get_player_url(pseudo, server, level, config['lang'])
        print(f"Player page URL: {player_url}")
        
        if player_url:
            response = requests.get(player_url)
            print(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = parse_player_data(response.text, player_url, config['lang'])
                await interaction.followup.send(embed=create_player_embed(data, config['lang']))
            else:
                await interaction.followup.send(embed=create_error_embed(config['lang'], player_url, response.status_code))
        else:
            await interaction.followup.send(embed=create_error_embed(config['lang'], base_url, 404))
    except KeyError as ke:
        await interaction.followup.send(f"KeyError: {ke} - Please check your language configuration.")
    except Exception as e:
        await interaction.followup.send(embed=create_error_embed(config['lang'], base_url, 500))
        print(f"Error: {e}")

def create_error_embed(lang, url, error_code):
    try:
        title = settings['language'][lang]['ERROR_TITLE']
        description = settings['language'][lang]['ERROR_DESCRIPTION']
    except KeyError:
        title = "Error"
        description = "An error occurred."
    embed = Embed(title=title, description=description)
    embed.add_field(name="URL", value=url)
    embed.add_field(name="Error Code", value=error_code)
    return embed

def get_player_url(pseudo, server, level, lang):
    base_search_url = settings['encyclopedia']['base_url'] + "/mmorpg/community/directories/character-pages"
    params = {
        "text": pseudo,
        "character_homeserv[]": server,
        "character_level_min": level if level else 1,
        "character_level_max": level if level else 200
    }
    search_url = base_search_url + "?" + "&".join([f"{key}={value}" for key, value in params.items()])
    print(f"Constructed search URL: {search_url}")
    
    response = requests.get(search_url)
    print(f"Search response status code: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        character_link = soup.find('a', class_='ak-directories-more')['href']
        return settings['encyclopedia']['base_url'] + character_link
    return None

def parse_player_data(html, link, lang):
    soup = BeautifulSoup(html, 'html.parser')
    data = {}
    main_info = soup.find('div', class_='ak-directories-main-infos')
    data['image'] = soup.find('div', class_='ak-entitylook')['style'].split('(')[1].split(')')[0]
    data['name'] = soup.find('h1', class_='ak-return-link').text.strip()
    data['level'] = main_info.find_next('div').text.strip().split()[1]
    data['race'] = main_info.contents[1].previous_element.strip()
    data['server'] = soup.find('span', class_='ak-directories-server-name').next_element.strip()
    data['link'] = link
    return data

def create_player_embed(data, lang):
    embed = Embed(title=data["name"], description=data.get("presentation", ""))
    embed.set_thumbnail(url=data["image"])
    embed.add_field(name="Level", value=data["level"], inline=True)
    embed.add_field(name="Race", value=data["race"], inline=True)
    embed.add_field(name="Server", value=data["server"], inline=True)
    return embed

if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
