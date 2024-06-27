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
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent
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
    logging.info(f'Logged in as {bot.user}')

@bot.tree.command(name="combine", description="Combine images into one long image")
async def combine(interaction: discord.Interaction):
    await interaction.response.send_message("Please upload the images you want to combine.", ephemeral=True)

    def check(msg):
        return msg.author == interaction.user and msg.attachments

    try:
        msg = await bot.wait_for('message', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await interaction.followup.send("You took too long to upload the images.", ephemeral=True)
        return

    attachments = msg.attachments

    if len(attachments) > 40:
        await interaction.followup.send("You can only combine up to 40 images.", ephemeral=True)
        return

    # Validate file extensions
    valid_extensions = ('.png', '.jpg', '.jpeg')
    for image in attachments:
        if not image.filename.lower().endswith(valid_extensions):
            await interaction.followup.send(f"File {image.filename} is not a valid PNG or JPG image.", ephemeral=True)
            return

    await interaction.followup.send("Combining images, please wait...", ephemeral=True)

    try:
        combined_image = await combine_images(attachments)
        file = discord.File(fp=combined_image, filename="combined_image.jpg")
        await interaction.followup.send("Here is your combined image:", file=file)
        logging.info("Combined image sent successfully")
    except Exception as e:
        logging.error(f"Error while combining images: {e}")
        await interaction.followup.send("An error occurred while combining the images.", ephemeral=True)

# Retrieve token from environment variable
bot_token = os.getenv('DISCORD_BOT_TOKEN')

# Run the bot with the token
bot.run(bot_token)
