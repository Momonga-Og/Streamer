import discord
from discord.ext import commands
from discord import app_commands

class PinSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='pin', description='Pin a specific message in a channel')
    @app_commands.describe(message_id='The ID of the message to pin', channel_name='The name of the channel to pin the message in')
    async def pin(self, interaction: discord.Interaction, message_id: str, channel_name: str):
        # Find the specified channel by name
        channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)
        
        if channel:
            try:
                # Fetch the specified message by ID from the specified channel
                message = await channel.fetch_message(int(message_id))
                
                # Pin the fetched message
                await message.pin()
                
                # Send a response indicating success
                await interaction.response.send_message(f'Message {message_id} pinned in {channel_name}.')
            except discord.NotFound:
                # Send a response if the message was not found
                await interaction.response.send_message(f'Message {message_id} not found.')
            except discord.Forbidden:
                # Send a response if the bot does not have permission to pin messages
                await interaction.response.send_message('I do not have permission to pin messages.')
            except discord.HTTPException as e:
                # Send a response if there was an HTTP error
                await interaction.response.send_message(f'Failed to pin message: {e}')
        else:
            # Send a response if the specified channel was not found
            await interaction.response.send_message(f'Channel {channel_name} not found.')

    @app_commands.command(name='pin-multi', description='Pin a specific message in multiple channels')
    @app_commands.describe(message_id='The ID of the message to pin', channel_names='The names of the channels to pin the message in')
    async def pin_multi(self, interaction: discord.Interaction, message_id: str, channel_names: str):
        channel_list = channel_names.split()
        channels = []
        if 'all' in channel_list:
            channels = interaction.guild.text_channels
        else:
            for channel_name in channel_list:
                channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)
                if channel:
                    channels.append(channel)
                else:
                    await interaction.followup.send(f'Channel {channel_name} not found.', ephemeral=True)
                    continue
        
        responses = []
        for channel in channels:
            try:
                message = await channel.fetch_message(int(message_id))
                await message.pin()
                responses.append(f'Message {message_id} pinned in {channel.name}.')
            except discord.NotFound:
                responses.append(f'Message {message_id} not found in {channel.name}.')
            except discord.Forbidden:
                responses.append(f'I do not have permission to pin messages in {channel.name}.')
            except discord.HTTPException as e:
                responses.append(f'Failed to pin message in {channel.name}: {e}')
        
        await interaction.response.send_message('\n'.join(responses))

    @app_commands.command(name='unpin', description='Unpin a specific message in the current channel')
    @app_commands.describe(message_id='The ID of the message to unpin')
    async def unpin(self, interaction: discord.Interaction, message_id: str):
        try:
            message = await interaction.channel.fetch_message(int(message_id))
            await message.unpin()
            await interaction.response.send_message(f'Message {message_id} unpinned.')
        except discord.NotFound:
            await interaction.response.send_message(f'Message {message_id} not found.')
        except discord.Forbidden:
            await interaction.response.send_message('I do not have permission to unpin messages.')
        except discord.HTTPException as e:
            await interaction.response.send_message(f'Failed to unpin message: {e}')

    @app_commands.command(name='listpins', description='List all currently pinned messages in the channel')
    async def listpins(self, interaction: discord.Interaction):
        pins = await interaction.channel.pins()
        if pins:
            pin_list = '\n'.join([f"{pin.id}: {pin.content}" for pin in pins])
            await interaction.response.send_message(f'Pinned messages:\n{pin_list}')
        else:
            await interaction.response.send_message('No pinned messages.')

async def setup(bot):
    await bot.add_cog(PinSettings(bot))
