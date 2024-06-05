import discord
from discord.ext import commands
from discord import app_commands

def setup(bot, config):

    @bot.tree.command(name='pin', description='Pin a specific message in a channel')
    @app_commands.describe(message_id='The ID of the message to pin', channel_name='The name of the channel to pin the message in')
    async def pin(interaction: discord.Interaction, message_id: int, channel_name: str):
        channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)
        if channel:
            try:
                message = await channel.fetch_message(message_id)
                await message.pin()
                await interaction.response.send_message(f'Message {message_id} pinned in {channel_name}.')
            except discord.NotFound:
                await interaction.response.send_message(f'Message {message_id} not found.')
            except discord.Forbidden:
                await interaction.response.send_message('I do not have permission to pin messages.')
            except discord.HTTPException as e:
                await interaction.response.send_message(f'Failed to pin message: {e}')
        else:
            await interaction.response.send_message(f'Channel {channel_name} not found.')

    @bot.tree.command(name='pin-multi', description='Pin a specific message in multiple channels')
    @app_commands.describe(message_id='The ID of the message to pin', channel_names='The names of the channels to pin the message in')
    async def pin_multi(interaction: discord.Interaction, message_id: int, channel_names: str):
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
                    await interaction.response.send_message(f'Channel {channel_name} not found.')
                    return
        
        for channel in channels:
            try:
                message = await channel.fetch_message(message_id)
                await message.pin()
                await interaction.response.send_message(f'Message {message_id} pinned in {channel.name}.')
            except discord.NotFound:
                await interaction.response.send_message(f'Message {message_id} not found in {channel.name}.')
            except discord.Forbidden:
                await interaction.response.send_message(f'I do not have permission to pin messages in {channel.name}.')
            except discord.HTTPException as e:
                await interaction.response.send_message(f'Failed to pin message in {channel.name}: {e}')

    @bot.tree.command(name='unpin', description='Unpin a specific message in the current channel')
    @app_commands.describe(message_id='The ID of the message to unpin')
    async def unpin(interaction: discord.Interaction, message_id: int):
        try:
            message = await interaction.channel.fetch_message(message_id)
            await message.unpin()
            await interaction.response.send_message(f'Message {message_id} unpinned.')
        except discord.NotFound:
            await interaction.response.send_message(f'Message {message_id} not found.')
        except discord.Forbidden:
            await interaction.response.send_message('I do not have permission to unpin messages.')
        except discord.HTTPException as e:
            await interaction.response.send_message(f'Failed to unpin message: {e}')

    @bot.tree.command(name='listpins', description='List all currently pinned messages in the channel')
    async def listpins(interaction: discord.Interaction):
        pins = await interaction.channel.pins()
        if pins:
            pin_list = '\n'.join([f"{pin.id}: {pin.content}" for pin in pins])
            await interaction.response.send_message(f'Pinned messages:\n{pin_list}')
        else:
            await interaction.response.send_message('No pinned messages.')

    class PinSettings(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

    bot.add_cog(PinSettings(bot))

    # Sync the command tree with Discord when the cog is ready
    @commands.Cog.listener()
    async def on_ready(self):
        await bot.tree.sync()
