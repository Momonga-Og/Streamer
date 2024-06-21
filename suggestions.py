import discord
from discord.ext import commands
from discord import app_commands
from io import BytesIO

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='suggest', description='Submit a suggestion')
    @app_commands.describe(suggestion='The suggestion text', image='Optional image attachment')
    async def suggest(self, interaction: discord.Interaction, suggestion: str, image: discord.Attachment = None):
        # Find the suggestions channel by name
        suggestions_channel = discord.utils.get(interaction.guild.text_channels, name='suggestions')

        if suggestions_channel:
            try:
                # Prepare the suggestion message
                content = f"Suggestion by {interaction.user.mention}:\n\n{suggestion}"
                files = []

                # Check if an image is attached
                if image:
                    # Ensure the file is an image
                    if image.content_type.startswith('image/'):
                        # Download the image
                        image_bytes = await image.read()
                        # Create a file-like object from the bytes
                        image_file = discord.File(BytesIO(image_bytes), filename=image.filename)
                        files.append(image_file)
                    else:
                        await interaction.response.send_message('The attachment is not a valid image.', ephemeral=True)
                        return

                # Send the suggestion as a new message in the suggestions channel
                suggestion_message = await suggestions_channel.send(content, files=files)

                # Add thumbs up and thumbs down reactions to the message
                await suggestion_message.add_reaction('👍')
                await suggestion_message.add_reaction('👎')

                # Respond to the user that the suggestion was submitted
                await interaction.response.send_message(f'Your suggestion has been submitted in {suggestions_channel.mention}.', ephemeral=True)
            except discord.Forbidden:
                # Send a response if the bot does not have permission to send messages or add reactions
                await interaction.response.send_message('I do not have permission to send messages or add reactions in the suggestions channel.', ephemeral=True)
            except discord.HTTPException as e:
                # Send a response if there was an HTTP error
                await interaction.response.send_message(f'Failed to submit suggestion: {e}', ephemeral=True)
        else:
            # Send a response if the suggestions channel was not found
            await interaction.response.send_message('Suggestions channel not found.', ephemeral=True)

async def setup(bot):
    await bot.add_cog(Suggestions(bot))
