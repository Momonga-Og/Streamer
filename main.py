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
ENCYCLOPEDIA = "https://www.dofus-touch.com/fr/mmorpg/encyclopedie"
IMAGE_URL = "https://static.ankama.com/dofus-touch/www/game/items/200"
SUFFIX = "?game=dofustouch"
URI = "http://www.krosmoz.com/fr/almanax"
DATES = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
SUPERTYPES = {
    1: "equipements", 2: "armes", 3: "equipements", 4: "equipements",
    5: "equipements", 6: "consommables", 9: "ressources",
    10: "equipements", 11: "equipements", 12: "familiers",
}

# Initialize the bot
intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Utility functions
def create_player_embed(data, lang):
    embed = Embed(title=data["name"], description=data.get("presentation", ""))
    embed.set_thumbnail(url=data["image"])
    embed.add_field(name="Level", value=data["level"], inline=True)
    embed.add_field(name="Race", value=data["race"], inline=True)
    embed.add_field(name="Server", value=data["server"], inline=True)
    if data.get("guild_name"):
        embed.add_field(name="Guild", value=f"[{data['guild_name']}]({data['guild_link']})", inline=True)
    if data.get("alliance_name"):
        embed.add_field(name="Alliance", value=f"[{data['alliance_name']}]({data['alliance_link']})", inline=True)
    return embed

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


def get_json(scope: str) -> dict:
    response = requests.post(
        f"https://proxyconnection.touch.dofus.com/data/map?lang=fr&v={VERSION}",
        json={"class": scope},
        headers={
            'origin': 'file://',
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US',
            'content-type': 'application/json',
            'authority': 'earlyproxy.touch.dofus.com',
            'user-agent': 'Mozilla/5.0 (Linux; Android 7.0; Nexus 5X Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.106 Mobile Safari/537.36'
        }
    )
    return response.json()

def parse_data(date: str, items: list, body: str) -> dict:
    root = BeautifulSoup(body, 'html.parser')
    event = root.select_one('#almanax_event_image')
    content = root.select('.mid')[2].contents
    image = root.select_one('#almanax_boss_image').contents
    description = root.select_one('#almanax_boss_desc').contents
    zodiac = root.select_one('.zodiac_more').contents
    offering = root.select('.more-infos-content')[1].contents
    name = ' '.join([elem.get_text() for elem in offering]).replace('\s+', ' ').strip().split(' ')[2:-6]
    quantity = int(''.join([elem.get_text() for elem in offering]).replace('\s+', ' ').strip().split(' ')[1])
    item = next((item for item in items if item['name'] == name), None)
    category = item['type'] if item else 9

    return {
        "MerydeName": description[0].contents[0].strip(),
        "MerydeDescription": description[1].strip(),
        "MerydeImage": image[0]['src'],
        "BonusDescription": ' '.join([elem.get_text() for elem in content[3].contents if elem.get('class') != 'more-infos']).replace('\s+', ' ').strip(),
        "BonusType": content[2].get_text().split(':')[1].strip(),
        "OfferingName": name,
        "OfferingQuantity": quantity,
        "OfferingImage": f"{IMAGE_URL}/{item['icon']}.png" if item else None,
        "OfferingURL": f"{ENCYCLOPEDIA}/{SUPERTYPES[category]}/{item['id']}-{name.replace(' ', '-')}" if item else None,
        "EventDescription": root.select_one('#almanax_event_desc').contents[-1].strip() if event else None,
        "EventImage": root.select_one('#almanax_event_image').contents[1]['src'] if event else None,
        "EventName": root.select_one('#almanax_event_desc').contents[1].strip() if event else None,
        "ZodiacName": zodiac[1].contents[0].strip(),
        "Date": date
    }

def get_player_page(base_url, pseudo, server, level):
    query_string = f"?text={pseudo}"
    if server:
        query_string += f"&character_homeserv[]={server}"
    if level:
        query_string += f"&character_level_min={level}&character_level_max={level}"
    else:
        query_string += "&character_level_min=1&character_level_max=200"

    url = f"{base_url}{query_string}"
    print(f"Constructed player page URL: {url}")
    response = requests.get(url)
    print(f"Player page response status code: {response.status_code}")

    if response.status_code == 200:
        return response.url
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

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'We have logged in as {bot.user}')

@bot.tree.command(name="whois")
async def whois(interaction: discord.Interaction, pseudo: str, level: int = None, server: str = None):
    await interaction.response.defer()
    pseudo = pseudo.lower()
    lang_map = {'fr': 0, 'en': 1}
    config = {'lang': 'en'}  # Default language is set to English
    lang_index = lang_map.get(config['lang'], 1)  # Default to English if language not found

    base_url = f"{settings['encyclopedia']['base_url']}/{settings['encyclopedia']['player_url'][lang_index]}"
    try:
        print(f"Using base URL: {base_url}")
        print(f"Parameters - Pseudo: {pseudo}, Server: {server}, Level: {level}")
        
        link = get_player_page(base_url, pseudo, server, level)
        print(f"Player page link: {link}")
        
        if link:
            response = requests.get(link)
            print(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = parse_player_data(response.text, link, config['lang'])
                await interaction.followup.send(embed=create_player_embed(data, config['lang']))
            else:
                await interaction.followup.send(embed=create_error_embed(config['lang'], link, response.status_code))
        else:
            await interaction.followup.send(embed=create_error_embed(config['lang'], base_url, 404))
    except KeyError as ke:
        await interaction.followup.send(f"KeyError: {ke} - Please check your language configuration.")
    except Exception as e:
        await interaction.followup.send(embed=create_error_embed(config['lang'], base_url, 500))
        print(f"Error: {e}")


@bot.tree.command(name="fetch_data")
async def fetch_data(interaction: discord.Interaction):
    data = get_json("Items")
    types = get_json("ItemTypes")
    items = [
        {
            "id": item["id"],
            "name": item["nameId"],
            "icon": item["iconId"],
            "type": types[item["typeId"]]["superTypeId"]
        }
        for item in data.values()
    ]
    result = get_almanaxs(items)
    json_data = json.dumps(dict(sorted(result.items())), indent=4)
    
    with open("./resources/year.json", "w", encoding="utf-8") as f:
        f.write(json_data)
    
    await interaction.followup.send("Data has been fetched and saved.")

@bot.tree.command(name="get_almanax")
async def get_almanax(interaction: discord.Interaction, date: str):
    with open("./resources/year.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    almanax_data = data.get(date)
    if (almanax_data):
        await interaction.followup.send(f"Almanax data for {date}:\n```json\n{json.dumps(almanax_data, indent=4)}```")
    else:
        await interaction.followup.send(f"No data found for {date}")

def get_almanaxs(items: list) -> dict:
    result = {}
    print("Fetching data...")

    for month in range(12):
        for day in range(DATES[month]):
            format_number = lambda nbr: f"{nbr + 1:02d}"
            date = f"2022-{format_number(month)}-{format_number(day)}"
            url = f"{URI}/{date}{SUFFIX}"
            response = requests.get(url)
            print(f"{date}: {response.status_code}")

            if response.status_code == 200:
                result[date] = parse_data(date, items, response.text)
            else:
                print(f"Invalid error code: {response.status_code}")

    return result

if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
