import discord
from discord.ext import commands
from discord import app_commands
import openai
import os

class OpenAIHelper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        openai.api_key = os.getenv('OPENAI_API_KEY')

    @app_commands.command(name="ask", description="Ask a question to the OpenAI helper")
    @app_commands.describe(question="The question you want to ask")
    async def ask(self, interaction: discord.Interaction, question: str):
        """Ask a question to the OpenAI API and get a response."""
        await interaction.response.defer()
        try:
            response = openai.Completion.create(
                engine="davinci",
                prompt=question,
                max_tokens=150
            )
            answer = response.choices[0].text.strip()
            await interaction.followup.send(f"**Question:** {question}\n**Answer:** {answer}")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(OpenAIHelper(bot))
