import os
import sqlite3
import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Connect to the database (or create it if it doesn't exist)
conn = sqlite3.connect('discord_bot.db')
cursor = conn.cursor()

# Create a table for storing user data if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    xp INTEGER NOT NULL,
    level INTEGER NOT NULL,
    time_spent INTEGER NOT NULL DEFAULT 0
)
''')
conn.commit()

# Define XP and level calculation
def calculate_level(xp):
    level = 0
    required_xp = 100
    while xp >= required_xp:
        xp -= required_xp
        level += 1
        required_xp *= 2
    return level

def elo_name(level):
    if 1 <= level <= 9:
        return "Iron Elo"
    elif 10 <= level <= 19:
        return "Bronze Elo"
    elif 20 <= level <= 29:
        return "Gold Elo"
    elif 30 <= level <= 39:
        return "Emerald Elo"
    elif 40 <= level <= 49:
        return "Plat Elo"
    elif level >= 50:
        return "Diamond Elo"
    return "Unranked"

# Function to add XP to a user
def add_xp(user_id, xp, time_spent=0):
    cursor.execute('SELECT xp, level, time_spent FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if user:
        new_xp = user[0] + xp
        new_time_spent = user[2] + time_spent
        new_level = calculate_level(new_xp)
        cursor.execute('UPDATE users SET xp = ?, level = ?, time_spent = ? WHERE user_id = ?', (new_xp, new_level, new_time_spent, user_id))
    else:
        new_xp = xp
        new_level = calculate_level(new_xp)
        new_time_spent = time_spent
        cursor.execute('INSERT INTO users (user_id, xp, level, time_spent) VALUES (?, ?, ?, ?)', (user_id, new_xp, new_level, new_time_spent))
    
    conn.commit()
    return new_level

# Function to retrieve user data
def get_user_data(user_id):
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    return cursor.fetchone()

# Function to create roles
async def create_roles(guild):
    roles = ["Iron Elo", "Bronze Elo", "Gold Elo", "Emerald Elo", "Plat Elo", "Diamond Elo"]
    for role in roles:
        if not discord.utils.get(guild.roles, name=role):
            await guild.create_role(name=role, permissions=discord.Permissions.none())

# Function to assign roles based on level
async def assign_role(member, level):
    elo = elo_name(level)
    role = discord.utils.get(member.guild.roles, name=elo)
    if role:
        # Remove previous Elo roles
        roles_to_remove = [r for r in member.roles if r.name in ["Iron Elo", "Bronze Elo", "Gold Elo", "Emerald Elo", "Plat Elo", "Diamond Elo"]]
        await member.remove_roles(*roles_to_remove)
        # Assign the new role
        await member.add_roles(role)

# Function to announce level up
async def announce_level_up(channel, member, level):
    embed = discord.Embed(
        title="🎉 Level Up! 🎉",
        description=f"{member.mention} has reached **Level {level}**!",
        color=discord.Color.gold()
    )
    embed.add_field(name="Elo", value=elo_name(level), inline=False)
    embed.set_thumbnail(url=member.avatar.url)
    await channel.send(embed=embed)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

# Track voice state changes
voice_states = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    for guild in bot.guilds:
        await create_roles(guild)
    check_voice_channels.start()
    await bot.tree.sync()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    user_id = str(message.author.id)
    user_data = get_user_data(user_id)
    new_level = add_xp(user_id, 10)  # Add 10 XP per message
    
    print(f"{message.author.name} has {user_data[1]} XP and is at level {user_data[2]} ({elo_name(user_data[2])})")
    
    if user_data and new_level > user_data[2]:  # Check if user has leveled up
        await assign_role(message.author, new_level)
        await announce_level_up(message.channel, message.author, new_level)
    
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    
    user_id = str(user.id)
    user_data = get_user_data(user_id)
    new_level = add_xp(user_id, 10)  # Add 10 XP per interaction
    
    print(f"{user.name} has {user_data[1]} XP and is at level {user_data[2]} ({elo_name(user_data[2])})")
    
    if user_data and new_level > user_data[2]:  # Check if user has leveled up
        await assign_role(user, new_level)
        await announce_level_up(reaction.message.channel, user, new_level)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    
    if before.channel is None and after.channel is not None:
        # User joined a voice channel
        voice_states[member.id] = discord.utils.utcnow()
    elif before.channel is not None and after.channel is None:
        # User left a voice channel
        if member.id in voice_states:
            start_time = voice_states.pop(member.id)
            time_spent = (discord.utils.utcnow() - start_time).total_seconds()
            user_id = str(member.id)
            user_data = get_user_data(user_id)
            new_level = add_xp(user_id, int(time_spent / 3600 * 100))  # Add 100 XP per hour spent
            print(f"{member.name} has {user_data[1]} XP and is at level {user_data[2]} ({elo_name(user_data[2])})")
            if user_data and new_level > user_data[2]:  # Check if user has leveled up
                await assign_role(member, new_level)
                await announce_level_up(before.channel, member, new_level)

@tasks.loop(minutes=1)
async def check_voice_channels():
    current_time = discord.utils.utcnow()
    for member_id, start_time in voice_states.items():
        time_spent = (current_time - start_time).total_seconds()
        if time_spent >= 3600:
            user_id = str(member_id)
            user_data = get_user_data(user_id)
            new_level = add_xp(user_id, 100)  # Add 100 XP for each hour spent
            voice_states[member_id] = current_time
            member = discord.utils.get(bot.get_all_members(), id=int(member_id))
            if member:
                print(f"{member.name} has {user_data[1]} XP and is at level {user_data[2]} ({elo_name(user_data[2])})")
                if user_data and new_level > user_data[2]:  # Check if user has leveled up
                    await assign_role(member, new_level)
                    await announce_level_up(member.guild.system_channel, member, new_level)

# Slash command to check XP and Elo
@tree.command(name="xp", description="Check your XP and Elo")
async def xp(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_data = get_user_data(user_id)
    
    if user_data:
        await interaction.response.send_message(f'{interaction.user.name}, you have {user_data[1]} XP and are at level {user_data[2]} ({elo_name(user_data[2])})')
    else:
        await interaction.response.send_message(f'{interaction.user.name}, you have no XP yet.')

# Slash command to check voice chat time in minutes
@tree.command(name="vc", description="Check your time spent in voice chat")
async def vc(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_data = get_user_data(user_id)
    
    if user_data:
        time_spent_minutes = user_data[3] / 60  # Convert seconds to minutes
        await interaction.response.send_message(f'{interaction.user.name}, you have spent {time_spent_minutes:.2f} minutes in voice chat.')
    else:
        await interaction.response.send_message(f'{interaction.user.name}, you have no voice chat time recorded yet.')

# Slash command to send a message through the bot, only visible to the bot owner
@tree.command(name="send_message", description="Send a message through the bot")
@app_commands.describe(message="The message to send")
async def send_message(interaction: discord.Interaction, message: str):
    # Replace 'YOUR_USER_ID' with the actual Discord user ID of the bot owner
    if interaction.user.id == 486652069831376943:
        await interaction.channel.send(message)
        await interaction.response.send_message("Message sent!", ephemeral=True)
    else:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

# Sync the commands with Discord in on_ready event

@bot.event
async def on_disconnect():
    conn.close()

# Add your bot token here
bot.run(DISCORD_BOT_TOKEN)
