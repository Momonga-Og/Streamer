import os
import sqlite3
import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import random

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Database handling class
class Database:
    def __init__(self, db_name='data/discord_bot.db'):
        self.db_name = db_name
        self.connect()

    def connect(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            xp INTEGER NOT NULL,
            level INTEGER NOT NULL,
            time_spent INTEGER NOT NULL DEFAULT 0
        )
        ''')
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            user_id TEXT,
            achievement TEXT,
            PRIMARY KEY (user_id, achievement)
        )
        ''')
        self.conn.commit()

    def close(self):
        self.conn.commit()
        self.conn.close()

    def add_xp(self, user_id, xp, time_spent=0):
        self.connect()
        self.cursor.execute('SELECT xp, level, time_spent FROM users WHERE user_id = ?', (user_id,))
        user = self.cursor.fetchone()

        if user:
            new_xp = user[0] + xp
            new_time_spent = user[2] + time_spent
            new_level = calculate_level(new_xp)
            self.cursor.execute('UPDATE users SET xp = ?, level = ?, time_spent = ? WHERE user_id = ?', (new_xp, new_level, new_time_spent, user_id))
        else:
            new_xp = xp
            new_level = calculate_level(new_xp)
            new_time_spent = time_spent
            self.cursor.execute('INSERT INTO users (user_id, xp, level, time_spent) VALUES (?, ?, ?, ?)', (user_id, new_xp, new_level, new_time_spent))

        self.conn.commit()
        self.close()
        return new_level

    def get_user_data(self, user_id):
        self.connect()
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user_data = self.cursor.fetchone()
        self.close()
        return user_data

    def get_top_users(self, limit=10):
        self.connect()
        self.cursor.execute('SELECT user_id, xp, level FROM users ORDER BY xp DESC LIMIT ?', (limit,))
        top_users = self.cursor.fetchall()
        self.close()
        return top_users

    def has_achievement(self, user_id, achievement):
        self.connect()
        self.cursor.execute('SELECT 1 FROM achievements WHERE user_id = ? AND achievement = ?', (user_id, achievement))
        has_it = self.cursor.fetchone() is not None
        self.close()
        return has_it

    def add_achievement(self, user_id, achievement):
        self.connect()
        self.cursor.execute('INSERT OR IGNORE INTO achievements (user_id, achievement) VALUES (?, ?)', (user_id, achievement))
        self.conn.commit()
        self.close()

# Initialize the database
db = Database()

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

# Function to announce achievements
async def announce_achievement(channel, member, achievement):
    embed = discord.Embed(
        title="🏆 Achievement Unlocked! 🏆",
        description=f"{member.mention} has unlocked **{achievement}**!",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.avatar.url)
    await channel.send(embed=embed)

# Function to check achievements
def check_achievements(user_id, xp):
    achievements = []
    if xp >= 1000 and not db.has_achievement(user_id, "1000 XP Milestone"):
        achievements.append("1000 XP Milestone")
    if xp >= 5000 and not db.has_achievement(user_id, "5000 XP Milestone"):
        achievements.append("5000 XP Milestone")
    return achievements

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
    user_data = db.get_user_data(user_id)
    previous_level = user_data[2] if user_data else 0
    
    new_level = db.add_xp(user_id, 10)  # Add 10 XP per message
    
    if user_data:
        print(f"{message.author.name} has {user_data[1]} XP and is at level {user_data[2]} ({elo_name(user_data[2])})")
    
    if new_level > previous_level:  # Check if user has leveled up
        await assign_role(message.author, new_level)
        await announce_level_up(message.channel, message.author, new_level)
    
    achievements = check_achievements(user_id, user_data[1] + 10 if user_data else 10)
    for achievement in achievements:
        db.add_achievement(user_id, achievement)
        await announce_achievement(message.channel, message.author, achievement)
    
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    
    user_id = str(user.id)
    user_data = db.get_user_data(user_id)
    previous_level = user_data[2] if user_data else 0
    
    new_level = db.add_xp(user_id, 10)  # Add 10 XP per interaction
    
    if user_data:
        print(f"{user.name} has {user_data[1]} XP and is at level {user_data[2]} ({elo_name(user_data[2])})")
    
    if new_level > previous_level:  # Check if user has leveled up
        await assign_role(user, new_level)
        await announce_level_up(reaction.message.channel, user, new_level)

    achievements = check_achievements(user_id, user_data[1] + 10 if user_data else 10)
    for achievement in achievements:
        db.add_achievement(user_id, achievement)
        await announce_achievement(reaction.message.channel, user, achievement)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    
    if before.channel is None and after.channel is not None:
        # User joined a voice channel
        voice_states[member.id] = discord.utils.utcnow()
        print(f"{member.name} joined {after.channel.name}")
    elif before.channel is not None and after.channel is None:
        # User left a voice channel
        if member.id in voice_states:
            start_time = voice_states.pop(member.id)
            time_spent = (discord.utils.utcnow() - start_time).total_seconds()
            print(f"{member.name} left {before.channel.name} after {time_spent} seconds")
            user_id = str(member.id)
            user_data = db.get_user_data(user_id)
            previous_level = user_data[2] if user_data else 0
            
            new_level = db.add_xp(user_id, int(time_spent / 3600 * 100), int(time_spent))  # Add 100 XP per hour spent
            
            if user_data:
                print(f"{member.name} has {user_data[1]} XP and is at level {user_data[2]} ({elo_name(user_data[2])})")
            
            if new_level > previous_level:  # Check if user has leveled up
                await assign_role(member, new_level)
                await announce_level_up(before.channel, member, new_level)

            achievements = check_achievements(user_id, user_data[1] + int(time_spent / 3600 * 100) if user_data else int(time_spent / 3600 * 100))
            for achievement in achievements:
                db.add_achievement(user_id, achievement)
                await announce_achievement(before.channel, member, achievement)

@tasks.loop(minutes=1)
async def check_voice_channels():
    current_time = discord.utils.utcnow()
    for member_id, start_time in voice_states.items():
        time_spent = (current_time - start_time).total_seconds()
        if time_spent >= 3600:
            user_id = str(member_id)
            user_data = db.get_user_data(user_id)
            previous_level = user_data[2] if user_data else 0
            
            new_level = db.add_xp(user_id, 100, 3600)  # Add 100 XP for each hour spent
            
            voice_states[member_id] = current_time
            member = discord.utils.get(bot.get_all_members(), id=int(member_id))
            if member:
                if user_data:
                    print(f"{member.name} has {user_data[1]} XP and is at level {user_data[2]} ({elo_name(user_data[2])})")
                
                if new_level > previous_level:  # Check if user has leveled up
                    await assign_role(member, new_level)
                    await announce_level_up(member.guild.system_channel, member, new_level)

                achievements = check_achievements(user_id, user_data[1] + 100 if user_data else 100)
                for achievement in achievements:
                    db.add_achievement(user_id, achievement)
                    await announce_achievement(member.guild.system_channel, member, achievement)

@tree.command(name="xp", description="Check your XP and Elo")
async def xp(interaction: discord.Interaction):
    try:
        await interaction.response.defer()  # Defer the response to avoid timeout
        
        user_id = str(interaction.user.id)
        user_data = db.get_user_data(user_id)

        if user_data:
            response_message = f'{interaction.user.name}, you have {user_data[1]} XP and are at level {user_data[2]} ({elo_name(user_data[2])})'
        else:
            response_message = f'{interaction.user.name}, you have no XP yet.'

        await interaction.followup.send(response_message)
    except discord.errors.NotFound as e:
        print(f"NotFound error: {e}")
        await interaction.followup.send("An error occurred: Unknown interaction.", ephemeral=True)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        await interaction.followup.send("An unexpected error occurred. Please try again later.", ephemeral=True)

# Slash command to check voice chat time in minutes
@tree.command(name="vc", description="Check your time spent in voice chat")
async def vc(interaction: discord.Interaction):
    await interaction.response.defer()  # Defer the response to avoid timeout
    
    user_id = str(interaction.user.id)
    user_data = db.get_user_data(user_id)
    
    if user_data:
        time_spent_minutes = user_data[3] / 60  # Convert seconds to minutes
        response_message = f'{interaction.user.name}, you have spent {time_spent_minutes:.2f} minutes in voice chat.'
    else:
        response_message = f'{interaction.user.name}, you have no voice chat time recorded yet.'
    
    await interaction.followup.send(response_message)

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

# Slash command to show leaderboard
@tree.command(name="leaderboard", description="Show the top users by XP")
async def leaderboard(interaction: discord.Interaction):
    await interaction.response.defer()  # Defer the response to avoid timeout

    top_users = db.get_top_users()
    embed = discord.Embed(title="🏆 Leaderboard 🏆", color=discord.Color.gold())
    for i, (user_id, xp, level) in enumerate(top_users, start=1):
        user = await bot.fetch_user(user_id)
        embed.add_field(name=f"{i}. {user.name}", value=f"XP: {xp}, Level: {level} ({elo_name(level)})", inline=False)
    
    await interaction.followup.send(embed=embed)

# Slash command to show user profile
@tree.command(name="profile", description="Show your profile or another user's profile")
@app_commands.describe(user="The user to show the profile for")
async def profile(interaction: discord.Interaction, user: discord.User = None):
    await interaction.response.defer()  # Defer the response to avoid timeout

    if user is None:
        user = interaction.user
    
    user_id = str(user.id)
    user_data = db.get_user_data(user_id)

    if user_data:
        embed = discord.Embed(title=f"{user.name}'s Profile", color=discord.Color.blue())
        embed.add_field(name="XP", value=user_data[1], inline=False)
        embed.add_field(name="Level", value=f"{user_data[2]} ({elo_name(user_data[2])})", inline=False)
        embed.add_field(name="Time Spent in Voice Chat", value=f"{user_data[3] / 60:.2f} minutes", inline=False)
    else:
        embed = discord.Embed(title=f"{user.name}'s Profile", description="No data available", color=discord.Color.blue())
    
    await interaction.followup.send(embed=embed)

# Slash command to show daily/weekly quests
@tree.command(name="quest", description="Show your daily/weekly quests")
async def quest(interaction: discord.Interaction):
    await interaction.response.defer()  # Defer the response to avoid timeout

    # Example quest data
    quests = [
        {"description": "Send 10 messages", "reward": "100 XP"},
        {"description": "Spend 1 hour in voice chat", "reward": "200 XP"},
    ]

    embed = discord.Embed(title="🗺️ Quests 🗺️", color=discord.Color.green())
    for quest in quests:
        embed.add_field(name=quest["description"], value=f"Reward: {quest['reward']}", inline=False)
    
    await interaction.followup.send(embed=embed)

# Slash command to show rewards
@tree.command(name="rewards", description="Show available rewards")
async def rewards(interaction: discord.Interaction):
    await interaction.response.defer()  # Defer the response to avoid timeout

    # Example rewards data
    rewards = [
        {"level": 5, "reward": "Custom Role"},
        {"level": 10, "reward": "Special Badge"},
    ]

    embed = discord.Embed(title="🎁 Rewards 🎁", color=discord.Color.purple())
    for reward in rewards:
        embed.add_field(name=f"Level {reward['level']}", value=reward["reward"], inline=False)
    
    await interaction.followup.send(embed=embed)

# Close the database connection on bot disconnect
@bot.event
async def on_disconnect():
    db.close()

# Add your bot token here
bot.run(DISCORD_BOT_TOKEN)
