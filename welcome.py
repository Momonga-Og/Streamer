import discord
from discord import File

def setup(bot, config):

    @bot.event
    async def on_member_join(member):
        print(f'Member joined: {member.name}')
        
        channel = discord.utils.get(member.guild.text_channels, name='welcome')
        
        if channel:
            print(f'Found welcome channel: {channel.name}')
            
            try:
                with open(config['welcome_image'], 'rb') as f:
                    picture = File(f)

                    # Build the welcome message
                    message = f"{config['welcome_message']}\n╰ ╮・ ┈ ┈ ┈ ┈ ┈ ┈ ┈ ┈ ↓ ↓\n"
                    message += f"╭ ╯ㅤ{member.mention}\n— — — — —  — — — —\n"
                    for ch in config['channels']:
                        channel_obj = discord.utils.get(member.guild.text_channels, name=ch['channel'])
                        if channel_obj:
                            message += f"📖 ⨯ ・{ch['description']} ⁠«{channel_obj.mention}»\n"
                        else:
                            message += f"📖 ⨯ ・{ch['description']} ⁠«{ch['channel']}»\n"
                    message += "— — — — —  — — — —\n"
                    message += f"⊹ ˚. 🌟┊⢀ ₊ ˚ ღ ˚. 🌍 ┊・ ˚.\n˚. ┊・ ⊹ ₊ ˚{config['footer']} ღ ˚. 🌠 ┊・"

                    await channel.send(message, file=picture)
                    print('Welcome message sent.')
            except KeyError as e:
                print(f'Error: Missing key {e} in config.json')
            except FileNotFoundError:
                print('Error: Welcome image file not found.')
        else:
            print('Welcome channel not found.')
