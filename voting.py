import discord
from discord.ext import commands
from discord import app_commands

class Voting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='vote', description='Create a vote for server decisions')
    @app_commands.describe(question='The question to vote on', options='Comma-separated list of options to vote on')
    async def vote(self, interaction: discord.Interaction, question: str, options: str):
        # Split the options into a list
        option_list = options.split(',')

        # Ensure there are between 2 and 10 options
        if len(option_list) < 2 or len(option_list) > 10:
            await interaction.response.send_message('Please provide between 2 and 10 options.', ephemeral=True)
            return

        # Create the embed for the vote
        embed = discord.Embed(title="Vote", description=question, color=discord.Color.blue())
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)

        # Add the options to the embed
        reactions = []
        for i, option in enumerate(option_list):
            emoji = chr(127462 + i)  # Regional indicator symbols (A, B, C, etc.)
            reactions.append(emoji)
            embed.add_field(name=f"{emoji} {option.strip()}", value='\u200b', inline=False)

        # Send the embed
        message = await interaction.channel.send(embed=embed)

        # Add the reactions for voting
        for reaction in reactions:
            await message.add_reaction(reaction)

        # Respond to the user that the vote was created
        await interaction.response.send_message('Vote created!', ephemeral=True)

async def setup(bot):
    await bot.add_cog(Voting(bot))
