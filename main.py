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
import sticky
import logging_system
from combine import combine_images

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.reactions = True
intents.voice_states = True

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
        await sticky.setup(self)
        await logging_system.setup(self)

        # Sync the command tree with Discord
        await self.tree.sync()

bot = MyBot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.tree.command(name="combine", description="Combine up to 40 images into one long image")
async def combine(interaction: discord.Interaction, images: commands.Greedy[discord.Attachment]):
    if not images:
        await interaction.response.send_message("Please attach images to combine.", ephemeral=True)
        return
    
    if len(images) > 40:
        await interaction.response.send_message("You can only combine up to 40 images.", ephemeral=True)
        return

    # Validate file extensions
    valid_extensions = ('.png', '.jpg', '.jpeg')
    for image in images:
        if not image.filename.lower().endswith(valid_extensions):
            await interaction.response.send_message(f"File {image.filename} is not a valid PNG or JPG image.", ephemeral=True)
            return

    combined_image = await combine_images(images)
    file = discord.File(fp=combined_image, filename="combined_image.png")
    await interaction.response.send_message("Here is your combined image:", file=file)

# Retrieve token from environment variable
bot_token = os.getenv('DISCORD_BOT_TOKEN')

# Run the bot with the token
bot.run(bot_token)
