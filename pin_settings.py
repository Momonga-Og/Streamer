import discord
from discord.ext import commands
from discord import app_commands

class PinSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='pin', description='Pin a specific message in a channel')
    @app_commands.describe(message_id='The ID of the message to pin', channel_name='The name of the channel to pin the message in')
    async def pin(self, interaction: discord.Interaction, message_id: str, channel_name: str):
        # Respond immediately to avoid interaction expiration
        await interaction.response.defer(ephemeral=True)

        # Find the specified channel by name
        channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)
        
        if channel:
            try:
                # Fetch the specified message by ID from the current channel
                message = await interaction.channel.fetch_message(int(message_id))
                
                # Send the message content as a new message in the target channel and pin it
                new_message = await channel.send(message.content)
                await new_message.pin()
                
                # Follow up with a response indicating success
                await interaction.followup.send(f'Message {message_id} pinned in {channel_name}.', ephemeral=True)
            except discord.NotFound:
                # Follow up with a response if the message was not found
                await interaction.followup.send(f'Message {message_id} not found.', ephemeral=True)
            except discord.Forbidden:
                # Follow up with a response if the bot does not have permission to pin messages
                await interaction.followup.send('I do not have permission to pin messages.', ephemeral=True)
            except discord.HTTPException as e:
                # Follow up with a response if there was an HTTP error
                await interaction.followup.send(f'Failed to pin message: {e}', ephemeral=True)
        else:
            # Follow up with a response if the specified channel was not found
            await interaction.followup.send(f'Channel {channel_name} not found.', ephemeral=True)

    @app_commands.command(name='pin-multi', description='Pin a specific message in multiple channels')
    @app_commands.describe(message_id='The ID of the message to pin', channel_names='The names of the channels to pin the message in, or "all" to pin in all channels')
    async def pin_multi(self, interaction: discord.Interaction, message_id: str, channel_names: str):
        # Respond immediately to avoid interaction expiration
        await interaction.response.defer(ephemeral=True)

        if channel_names.lower() == 'all':
            channels = interaction.guild.text_channels
        else:
            channel_list = channel_names.split()
            channels = []
            for channel_name in channel_list:
                channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)
                if channel:
                    channels.append(channel)
                else:
                    await interaction.followup.send(f'Channel {channel_name} not found.', ephemeral=True)
                    continue
        
        responses = []
        try:
            # Fetch the specified message by ID from the current channel
            message = await interaction.channel.fetch_message(int(message_id))
            for channel in channels:
                try:
                    # Send the message content as a new message in each target channel and pin it
                    new_message = await channel.send(message.content)
                    await new_message.pin()
                    responses.append(f'Message {message_id} pinned in {channel.name}.')
                except discord.Forbidden:
                    responses.append(f'I do not have permission to pin messages in {channel.name}.')
                except discord.HTTPException as e:
                    responses.append(f'Failed to pin message in {channel.name}: {e}')
        except discord.NotFound:
            responses.append(f'Message {message_id} not found in the current channel.')
        
        await interaction.followup.send('\n'.join(responses), ephemeral=True)

    @app_commands.command(name='unpin', description='Unpin a specific message in the current channel')
    @app_commands.describe(message_id='The ID of the message to unpin')
    async def unpin(self, interaction: discord.Interaction, message_id: str):
        # Respond immediately to avoid interaction expiration
        await interaction.response.defer(ephemeral=True)

        try:
            message = await interaction.channel.fetch_message(int(message_id))
            await message.unpin()
            await interaction.followup.send(f'Message {message_id} unpinned.', ephemeral=True)
        except discord.NotFound:
            await interaction.followup.send(f'Message {message_id} not found.', ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send('I do not have permission to unpin messages.', ephemeral=True)
        except discord.HTTPException as e:
            await interaction.followup.send(f'Failed to unpin message: {e}', ephemeral=True)

    @app_commands.command(name='listpins', description='List all currently pinned messages in the channel')
    async def listpins(self, interaction: discord.Interaction):
        # Respond immediately to avoid interaction expiration
        await interaction.response.defer(ephemeral=True)

        try:
            pins = await interaction.channel.pins()
            if pins:
                pin_list = '\n'.join([f"{pin.id}: {pin.content}" for pin in pins])
                await interaction.followup.send(f'Pinned messages:\n{pin_list}', ephemeral=True)
            else:
                await interaction.followup.send('No pinned messages.', ephemeral=True)
        except discord.HTTPException as e:
            await interaction.followup.send(f'Failed to list pinned messages: {e}', ephemeral=True)

async def setup(bot, config):
    await bot.add_cog(PinSettings(bot))
