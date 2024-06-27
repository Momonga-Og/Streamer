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
async def combine(interaction: discord.Interaction, attachment1: discord.Attachment = None, attachment2: discord.Attachment = None, attachment3: discord.Attachment = None,
                  attachment4: discord.Attachment = None, attachment5: discord.Attachment = None, attachment6: discord.Attachment = None,
                  attachment7: discord.Attachment = None, attachment8: discord.Attachment = None, attachment9: discord.Attachment = None,
                  attachment10: discord.Attachment = None, attachment11: discord.Attachment = None, attachment12: discord.Attachment = None,
                  attachment13: discord.Attachment = None, attachment14: discord.Attachment = None, attachment15: discord.Attachment = None,
                  attachment16: discord.Attachment = None, attachment17: discord.Attachment = None, attachment18: discord.Attachment = None,
                  attachment19: discord.Attachment = None, attachment20: discord.Attachment = None, attachment21: discord.Attachment = None,
                  attachment22: discord.Attachment = None, attachment23: discord.Attachment = None, attachment24: discord.Attachment = None,
                  attachment25: discord.Attachment = None, attachment26: discord.Attachment = None, attachment27: discord.Attachment = None,
                  attachment28: discord.Attachment = None, attachment29: discord.Attachment = None, attachment30: discord.Attachment = None,
                  attachment31: discord.Attachment = None, attachment32: discord.Attachment = None, attachment33: discord.Attachment = None,
                  attachment34: discord.Attachment = None, attachment35: discord.Attachment = None, attachment36: discord.Attachment = None,
                  attachment37: discord.Attachment = None, attachment38: discord.Attachment = None, attachment39: discord.Attachment = None,
                  attachment40: discord.Attachment = None):
    attachments = [attachment for attachment in [attachment1, attachment2, attachment3, attachment4, attachment5, attachment6,
                                                 attachment7, attachment8, attachment9, attachment10, attachment11, attachment12,
                                                 attachment13, attachment14, attachment15, attachment16, attachment17, attachment18,
                                                 attachment19, attachment20, attachment21, attachment22, attachment23, attachment24,
                                                 attachment25, attachment26, attachment27, attachment28, attachment29, attachment30,
                                                 attachment31, attachment32, attachment33, attachment34, attachment35, attachment36,
                                                 attachment37, attachment38, attachment39, attachment40] if attachment]

    if not attachments:
        await interaction.response.send_message("Please attach images to combine.", ephemeral=True)
        return
    
    if len(attachments) > 40:
        await interaction.response.send_message("You can only combine up to 40 images.", ephemeral=True)
        return

    # Validate file extensions
    valid_extensions = ('.png', '.jpg', '.jpeg')
    for image in attachments:
        if not image.filename.lower().endswith(valid_extensions):
            await interaction.response.send_message(f"File {image.filename} is not a valid PNG or JPG image.", ephemeral=True)
            return

    combined_image = await combine_images(attachments)
    file = discord.File(fp=combined_image, filename="combined_image.png")
    await interaction.response.send_message("Here is your combined image:", file=file)

# Retrieve token from environment variable
bot_token = os.getenv('DISCORD_BOT_TOKEN')

# Run the bot with the token
bot.run(bot_token)
