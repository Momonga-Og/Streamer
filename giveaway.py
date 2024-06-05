import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import datetime

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_giveaways = {}

    @app_commands.command(name='start_giveaway', description='Start a giveaway')
    @app_commands.describe(duration='Duration of the giveaway in minutes', prize='The prize for the giveaway')
    async def start_giveaway(self, interaction: discord.Interaction, duration: int, prize: str):
        end_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=duration)
        embed = discord.Embed(title="🎉 **Giveaway Started!** 🎉", description=f"**Prize**: {prize}\n\nReact with 🎉 to enter!\n\n**Ends at**: {end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC", color=discord.Color.blue())
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/762387665989091348/871290592215195648/giveaway.png")
        embed.set_footer(text="Good luck!")
        
        giveaway_message = await interaction.channel.send(embed=embed)
        await giveaway_message.add_reaction('🎉')
        
        self.active_giveaways[giveaway_message.id] = {
            'end_time': end_time,
            'prize': prize,
            'message': giveaway_message,
            'channel': interaction.channel
        }
        
        self.check_giveaway.start(giveaway_message.id)
        
        await interaction.response.send_message('Giveaway started!', ephemeral=True)

    @tasks.loop(seconds=30)
    async def check_giveaway(self, message_id):
        giveaway = self.active_giveaways.get(message_id)
        if giveaway and datetime.datetime.utcnow() >= giveaway['end_time']:
            channel = giveaway['channel']
            message = giveaway['message']
            
            message = await channel.fetch_message(message.id)
            users = [user async for user in message.reactions[0].users() if not user.bot]
            
            if users:
                winner = random.choice(users)
                await channel.send(f"🎉 Congratulations {winner.mention}! You won the prize: **{giveaway['prize']}** 🎉")
                try:
                    await winner.send(f"🎉 Congratulations! You won the prize: **{giveaway['prize']}** in the giveaway! 🎉")
                except discord.Forbidden:
                    await channel.send(f"Couldn't send a private message to {winner.mention}.")
            else:
                await channel.send("No valid entries, no winner could be determined.")
            
            del self.active_giveaways[message_id]
            self.check_giveaway.stop()

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
