import discord
from discord.ext import commands
import json
import os
import welcome
import pin_settings
import suggestions
import voting
import giveaway
import tickets

intents = discord.Intents.default()
intents.members = True
intents.messages = True

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = None

    async def setup_hook(self):
        # Load configuration
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # Import functionalities
        welcome.setup(self, self.config)
        await pin_settings.setup(self, self.config)
        await suggestions.setup(self)
        await voting.setup(self)
        await giveaway.setup(self)
        await tickets.setup(self)

        # Sync the command tree with Discord
        await self.tree.sync()

bot = MyBot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Retrieve token from environment variable
bot_token = os.getenv('DISCORD_BOT_TOKEN')

# Run the bot with the token
bot.run(bot_token)
