
import discord
from discord.ext import commands
from discord import Intents
from datetime import datetime, timedelta
import asyncio
import configparser
import time

def load_config(file_path):
            config = configparser.ConfigParser()
            config.read(file_path)
            return config['config']

config = load_config('config.txt')

      
        # Accessing configuration variables
BOT_TOKEN = config['BOT_TOKEN']
REQUIRED_ROLE_ID_HERE = int(config['REQUIRED_ROLE_ID_HERE'])
REQUIRED_ROLE_ID_EVERYONE = int(config['REQUIRED_ROLE_ID_EVERYONE'])
SLOT_OWNER_HERE_ROLE_ID = int(config['SLOT_OWNER_HERE_ROLE_ID'])
SLOT_OWNER_EVERYONE_ROLE_ID = int(config['SLOT_OWNER_EVERYONE_ROLE_ID'])
OWNER = int(config['OWNER'])
ADDITIONAL_ID = int(config['ADDITIONAL_ID'])
CATEGORY_ID_1 = int(config['CATEGORY_ID_1'])  # slots #1 category
CATEGORY_ID_2 = int(config['CATEGORY_ID_2'])  # slots #2 category
CATEGORY_ID_3 = int(config['CATEGORY_ID_3'])  # slots #3 category





intents = Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix=',', intents=intents)
client.remove_command('help')  # This disables the default help command

# Data storage using a dictionary (consider a database for persistence)
user_slots = {}  # Track users and their slot details

async def check_staff(ctx):
    staff_role = ctx.guild.get_role(OWNER)
    additional_role = ctx.guild.get_role(ADDITIONAL_ID)

    if staff_role in ctx.author.roles or additional_role in ctx.author.roles:
        return True
    else:
        await ctx.send("You are not whitelisted to use this bot.")
        return False


@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.command()
async def info(ctx):
    embed = discord.Embed(title="Slot Commands", description="Here are the available commands for managing slots:", color=0xBF55EC)
    embed.set_thumbnail(url="https://i.postimg.cc/3NCT11GW/static-3.png")
    embed.add_field(name=",create", value="Create a new slot interactively.\nExample: `,create` and follow the prompts. type stop at any moment to cancel the process", inline=False)
    embed.add_field(name=",addpings", value="Add pings to an existing slot. Usage: `,addpings <user_id> <number_of_pings>`\nExample: `,addpings @username 3`", inline=False)
    embed.add_field(name=",renew", value="Renew an existing slot. Usage: `,renew <user_id>`\nExample: `,renew @username`", inline=False)
    embed.add_field(name=",revoke", value="Revoke a slot. Usage: `,revoke <user_id> [reason]`\nExample: `,revoke @username Spamming`", inline=False)
    embed.add_field(name=",pingcount", value="Check the number of pings left for your slot. Usage: `,pingcount`\nExample: `,pingcount`", inline=False)
    embed.add_field(name=",hold", value="Hold a user's slot to prevent them from using it. Usage: `,hold <userid>`\nExample: `,hold <userid>`", inline=False)
    embed.add_field(name=",release", value="Release a slot from a user. Usage: `,release <user_id>`\nExample: `,release <userid>`", inline=False)
    
    # Adding developer credits
    embed.add_field(name="Developer Credits", value="Bot developed by vxyzp.", inline=False)
    
    await ctx.send(embed=embed)



@client.command()
async def create(ctx):
    if not await check_staff(ctx):
        return

    # Ask for category
    category_id = None
    while category_id is None:
        category_prompt = await ctx.send("Please select a category:\n1. Slots #1\n2. Slots #2\n3. Slots #3\n*Tip:* Type 'stop' at any point of this process to cancel.")

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        try:
            category_response = await client.wait_for('message', check=check, timeout=30)
            if category_response.content.lower() == "stop":
                await ctx.send("Command process cancelled.")
                return

            if category_response.content == "1":
                category_id = int(config['CATEGORY_ID_1'])
            elif category_response.content == "2":
                category_id = int(config['CATEGORY_ID_2'])
            elif category_response.content == "3":
                category_id = int(config['CATEGORY_ID_3'])
            else:
                await ctx.send("Invalid category. Please enter 1, 2, or 3.")
                await category_prompt.delete()
                continue  # Loop again to ask for category

        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Command process cancelled.")
            return

    # Ask for time
    while True:
        await ctx.send("Please enter the duration (e.g.,`1d`, `1h`, or `lifetime`)")

        try:
            time_response = await client.wait_for('message', check=check, timeout=30)
            if time_response.content.lower() == "stop":
                await ctx.send("Command process cancelled.")
                return

            time = time_response.content
            if time.lower() == "lifetime":
                expiration_time = None
                break
            else:
                try:
                    if time.endswith("d"):
                        days = int(time[:-1])
                        time_in_seconds = days * 86400
                    elif time.endswith("h"):
                        hours = int(time[:-1])
                        time_in_seconds = hours * 3600
                    else:
                        time_in_seconds = int(time) * 3600  # Assuming input is in hours if no suffix
                    expiration_time = datetime.now() + timedelta(seconds=time_in_seconds)
                    break  # Exit loop if valid
                except ValueError:
                    await ctx.send("Invalid time format. Please enter a valid duration.")

        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Command process cancelled.")
            return

    # Ask for mention type
    while True:
        await ctx.send("Please enter the mention type (`here` or `everyone`)")

        try:
            mention_response = await client.wait_for('message', check=check, timeout=30)
            if mention_response.content.lower() == "stop":
                await ctx.send("Command process cancelled.")
                return

            if mention_response.content in ["here", "everyone"]:
                mention_type = mention_response.content
                break  # Exit loop if valid
            else:
                await ctx.send("Invalid mention type. Please enter `here` or `everyone`.")

        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Command process cancelled.")
            return

    # Ask for user ID
    while True:
        await ctx.send("Please mention the user (or provide their ID)")

        try:
            user_response = await client.wait_for('message', check=check, timeout=30)
            if user_response.content.lower() == "stop":
                await ctx.send("Command process cancelled.")
                return

            # Fetch user
            user_id = int(user_response.content.strip("<@!>"))
            user = await ctx.guild.fetch_member(user_id)
            break  # Exit loop if valid

        except (ValueError, discord.NotFound):
            await ctx.send("Invalid user. Please mention a valid user.")
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Command process cancelled.")
            return

    # Ask for number of pings
    while True:
        await ctx.send("Please enter the number of pings allowed.")

        try:
            pings_response = await client.wait_for('message', check=check, timeout=30)
            if pings_response.content.lower() == "stop":
                await ctx.send("Command process cancelled.")
                return

            number_of_pings = int(pings_response.content)
            break  # Exit loop if valid

        except ValueError:
            await ctx.send("Invalid number of pings. Please enter a valid integer.")
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Command process cancelled.")
            return

    # Create channel and set permissions as before
    category = ctx.guild.get_channel(category_id)
    if not category:
        await ctx.send("Invalid category ID.")
        return

    channel_name = user.name
    channel = await ctx.guild.create_text_channel(channel_name, category=category)

    # Set permissions
    overwrite = discord.PermissionOverwrite()
    overwrite.send_messages = False
    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

    overwrite = discord.PermissionOverwrite()
    overwrite.send_messages = True
    await channel.set_permissions(user, overwrite=overwrite)

    # Store slot details
    user_slots[user.id] = {
        'channel_id': channel.id,
        'expiration_time': expiration_time,
        'pings_left': number_of_pings,
        'warnings': 0,
        'mention_type': mention_type
    }

    slot_owner_role_id = config['SLOT_OWNER_HERE_ROLE_ID'] if mention_type == "here" else config['SLOT_OWNER_EVERYONE_ROLE_ID']
    slot_owner_role = ctx.guild.get_role(slot_owner_role_id)
    if slot_owner_role:
        await user.add_roles(slot_owner_role)

    # Constructing the embed
    embed = discord.Embed(title="SLOT INFORMATION", description="Details of the slot created:", color=0xAA00FF)
    embed.set_thumbnail(url=user.avatar.url)
    embed.add_field(name="User ID", value=user.id, inline=True)
    embed.add_field(name="Username", value=user.name, inline=True)
    embed.add_field(name="Creation Time", value=datetime.now().strftime('%Y-%m-%d'), inline=False)
    if expiration_time:
        time_left = expiration_time - datetime.now()
        if time_left.days > 0:
            time_str = f"{time_left.days} days"
        else:
            hours_left = time_left.seconds // 3600
            minutes_left = (time_left.seconds % 3600) // 60
            time_str = f"{hours_left} hours, {minutes_left} minutes"
        
        embed.add_field(name="Expiration Time", value=f"{expiration_time.strftime('%Y-%m-%d')} (in {time_str} from now)", inline=False)
    else:
        embed.add_field(name="Expiration Time", value="Never (lifetime)", inline=False)

    embed.add_field(name="Pings Allowed", value=f"{number_of_pings} ({mention_type} pings)", inline=False)

    # Sending the embed
    await channel.send(embed=embed)
    await channel.send(f"{user.mention}, your slot has been created!")












@client.command()
async def addpings(ctx, user_id, number_of_pings):
    if not await check_staff(ctx):
        return

    # Fetch user
    user = await ctx.guild.fetch_member(int(user_id))
    # Add specified number of pings to the user's data
    if user.id in user_slots:
        user_slots[user.id]['pings_left'] += int(number_of_pings)
        blue_embed = discord.Embed(title="Confirmation", description="Pings have been added successfully.", color=0x0000FF).set_thumbnail(url="https://i.postimg.cc/3NCT11GW/static-3.png") 

        await ctx.send(embed=blue_embed)
    # Add confirmation message to the slot
        channel_id = user_slots[user.id]['channel_id']
        channel = ctx.guild.get_channel(channel_id)
        pings_added = int(number_of_pings)  # Convert the number of pings to an integer
        confirmation_embed = discord.Embed(title="Pings Added", description=f"{pings_added} pings have been successfully added by {ctx.author.mention}. use the command **,pingcount** to see how many pings you have left.", color=0x0000FF).set_thumbnail(url="https://i.postimg.cc/3NCT11GW/static-3.png")
        await channel.send(embed=confirmation_embed)



@client.command()
async def renew(ctx, user_id):
    if not await check_staff(ctx):
        return

    # Fetch user
    user = await ctx.guild.fetch_member(int(user_id))
    if user.id in user_slots:
        overwrite = discord.PermissionOverwrite()
        overwrite.send_messages = True
        channel_id = user_slots[user.id]['channel_id']
        channel = ctx.guild.get_channel(channel_id)
        await channel.set_permissions(user, overwrite=overwrite)

        # Create the embed object
        embed = discord.Embed(title="SLOT RENEWED", description=f"This slot has been successfully renewed by {ctx.author.mention}. Remember {user.mention}, when a slot is renewed your pings are automatically set to 0! Pinging will get your slot revoked again. DM a <@1203295927310360617> member if you wish to purchase more pings.", color=0x00ff00)
        embed.set_thumbnail(url="https://i.postimg.cc/25vXn6hS/static-4.png")

        # Send the message and embed to the channel
        new_embed = discord.Embed(title="SLOT RENEWED", description=f"Slot successfully renewed by {ctx.author.mention}", color=0x00ff00)
        new_embed.set_thumbnail(url="https://i.postimg.cc/25vXn6hS/static-4.png")

        # Send the message and new embed to the channel
        await ctx.send(embed=new_embed)
        await channel.send(embed=embed)

        # Reset pings left to 0
        user_slots[user.id]['pings_left'] = 0


        

@client.event
async def on_message(message):
    if message.author == client.user:
        return  # Ignore self messages

    # Check for @here or @everyone mentions
    if "@here" in message.content or "@everyone" in message.content:
        user_id = message.author.id
        if user_id in user_slots:
            pings_left = user_slots[user_id].get('pings_left', 0)
            mention_type = user_slots[user_id].get('mention_type', None)
            if pings_left > 0:
                if mention_type == "here" and "@everyone" in message.content:
                    # Warn user for using @everyone in a @here slot
                    user_slots[user_id]['warnings'] += 1
                    await message.channel.send(f"{message.author.mention}, you cannot use @everyone in a @here slot.")
                    await message.channel.send(f"You have {2 - user_slots[user_id]['warnings']} warnings left.")
                    if user_slots[user_id]['warnings'] >= 2:
                        await revoke_slot(message.author)
                elif mention_type == "everyone" and "@here" in message.content:
                    # Warn user for using @here in an @everyone slot
                    user_slots[user_id]['warnings'] += 1
                    await message.channel.send(f"{message.author.mention}, you cannot use @here in an @everyone slot.")
                    await message.channel.send(f"You have {2 - user_slots[user_id]['warnings']} warnings left.")
                    if user_slots[user_id]['warnings'] >= 2:
                        await revoke_slot(message.author)
                else:
                    user_slots[user_id]['pings_left'] -= 1
                    await message.channel.send(f"{message.author.mention}, you have {pings_left - 1} pings left.")
            else:
                await message.channel.send(f"{message.author.mention}, you have used all your pings.")
                # Revoke user's ability to send messages in the channel
                await revoke_slot(message.author)
        else:
            await message.channel.send(f"{message.author.mention}, you don't have a slot.")

    await client.process_commands(message)

async def revoke_slot(user):
    user_id = user.id
    overwrite = discord.PermissionOverwrite()
    overwrite.send_messages = False
    channel_id = user_slots[user_id]['channel_id']
    channel = user.guild.get_channel(channel_id)
    await channel.set_permissions(user, overwrite=overwrite)
    await channel.send(f"{user.mention}, your slot has been revoked. This slot will automatically be deleted in 12 hours.")
    # Send confirmation embed to user
    embed = discord.Embed(title="SLOT REVOKED", description=f"Your slot has been revoked. This slot will automatically be deleted in 12 hours.", color=0xff0000)
    await user.send(embed=embed)
    del user_slots[user_id]
    # Remove slot owner role
    slot_owner_role_id = None
    if user_slots[user_id]['mention_type'] == "here":
        slot_owner_role_id = SLOT_OWNER_HERE_ROLE_ID
    elif user_slots[user_id]['mention_type'] == "everyone":
        slot_owner_role_id = SLOT_OWNER_EVERYONE_ROLE_ID
    if slot_owner_role_id:
        slot_owner_role = user.guild.get_role(slot_owner_role_id)
        if slot_owner_role:
            await user.remove_roles(slot_owner_role)

@client.command()
async def revoke(ctx, user_id, *reason):
    if not await check_staff(ctx):
        return

    user_id = int(user_id)
    user = await ctx.guild.fetch_member(user_id)

    if user.id in user_slots:
        # Remove required roles
        required_here_role = ctx.guild.get_role(REQUIRED_ROLE_ID_HERE)
        required_everyone_role = ctx.guild.get_role(REQUIRED_ROLE_ID_EVERYONE)
        slot_owner_here_role = ctx.guild.get_role(SLOT_OWNER_HERE_ROLE_ID)
        slot_owner_everyone_role = ctx.guild.get_role(SLOT_OWNER_EVERYONE_ROLE_ID)

        # Fetch roles using role IDs
        required_here_role = ctx.guild.get_role(REQUIRED_ROLE_ID_HERE)
        required_everyone_role = ctx.guild.get_role(REQUIRED_ROLE_ID_EVERYONE)
        slot_owner_here_role = ctx.guild.get_role(SLOT_OWNER_HERE_ROLE_ID)
        slot_owner_everyone_role = ctx.guild.get_role(SLOT_OWNER_EVERYONE_ROLE_ID)

        if required_here_role:
            await user.remove_roles(required_here_role)
        if required_everyone_role:
            await user.remove_roles(required_everyone_role)
        if slot_owner_here_role:
            await user.remove_roles(slot_owner_here_role)
        if slot_owner_everyone_role:
            await user.remove_roles(slot_owner_everyone_role)

        # Remove slot permissions
        channel_id = user_slots[user.id]['channel_id']
        channel = ctx.guild.get_channel(channel_id)
        overwrite = discord.PermissionOverwrite()
        overwrite.send_messages = False
        await channel.set_permissions(user, overwrite=overwrite)

        
        revoke_embed = discord.Embed(title="SLOT REVOKED", description=f"Your slot has been revoked by {ctx.author.mention}. If you think this is a mistake please contact a staff member.", color=0xff0000)
        revoke_embed.set_thumbnail(url="https://i.postimg.cc/Hs6GLV9G/static-5.png")

        if reason:
            revoke_embed.add_field(name="Reason", value=" ".join(reason), inline=False)
        revoke_embed.set_footer(text="Slot will automatically be deleted in 12 hours.")

        # Send the revoke embed to the slot channel
        await channel.send(embed=revoke_embed)

        # Send a separate embed to the command issuer
        confirmation_embed = discord.Embed(title="SLOT REVOKED", description=f"The slot of {user.mention} has been successfully revoked.", color=0xff0000)
        confirmation_embed.set_thumbnail(url="https://i.postimg.cc/Hs6GLV9G/static-5.png")
        if reason:
            confirmation_embed.add_field(name="Reason", value=" ".join(reason), inline=False)
        confirmation_embed.set_footer(text="Slot will automatically be deleted in 12 hours.")

        await ctx.send(embed=confirmation_embed)

        # Delete the slot after 12 hours
        await asyncio.sleep(43200)  # 12 hours
        await channel.delete()
    else:
        await ctx.send(f"User {user.name} ({user.id}) does not have a slot.")

@client.command()
async def hold(ctx, user_id):
    if not await check_staff(ctx):
        return

    user_id = int(user_id)
    user = await ctx.guild.fetch_member(user_id)

    if user.id in user_slots:
        # Remove required roles
        required_here_role = ctx.guild.get_role(REQUIRED_ROLE_ID_HERE)
        required_everyone_role = ctx.guild.get_role(REQUIRED_ROLE_ID_EVERYONE)
        slot_owner_here_role = ctx.guild.get_role(SLOT_OWNER_HERE_ROLE_ID)
        slot_owner_everyone_role = ctx.guild.get_role(SLOT_OWNER_EVERYONE_ROLE_ID)

        # Fetch roles using role IDs
        required_here_role = ctx.guild.get_role(REQUIRED_ROLE_ID_HERE)
        required_everyone_role = ctx.guild.get_role(REQUIRED_ROLE_ID_EVERYONE)
        slot_owner_here_role = ctx.guild.get_role(SLOT_OWNER_HERE_ROLE_ID)
        slot_owner_everyone_role = ctx.guild.get_role(SLOT_OWNER_EVERYONE_ROLE_ID)

        if required_here_role:
            await user.remove_roles(required_here_role)
        if required_everyone_role:
            await user.remove_roles(required_everyone_role)
        if slot_owner_here_role:
            await user.remove_roles(slot_owner_here_role)
        if slot_owner_everyone_role:
            await user.remove_roles(slot_owner_everyone_role)

        # Remove slot permissions
        channel_id = user_slots[user.id]['channel_id']
        channel = ctx.guild.get_channel(channel_id)
        overwrite = discord.PermissionOverwrite()
        overwrite.send_messages = False
        await channel.set_permissions(user, overwrite=overwrite)

        
        hold_embed = discord.Embed(title="SLOT ON HOLD", description=f"This slot has been put on hold due to a report being opened against the user. Please do not trade with the owner of this slot until the case has been resolved", color=0x000000)
        hold_embed.set_thumbnail(url="https://i.postimg.cc/Hs6GLV9G/static-5.png")

        # Send the revoke embed to the slot channel
        await channel.send(embed=hold_embed)

        # Send a separate embed to the command issuer
        confirmation_embed = discord.Embed(title="SLOT ON HOLD", description=f"The slot of {user.mention} has been successfully put on hold.", color=0x000000)
        confirmation_embed.set_thumbnail(url="https://i.postimg.cc/Hs6GLV9G/static-5.png")

        await ctx.send(embed=confirmation_embed)

    else:
        await ctx.send(f"User {user.name} ({user.id}) does not have a slot.")

@client.command()
async def release(ctx, user_id):
    if not await check_staff(ctx):
        return

    # Fetch user
    user = await ctx.guild.fetch_member(int(user_id))
    if user.id in user_slots:
        overwrite = discord.PermissionOverwrite()
        overwrite.send_messages = True
        channel_id = user_slots[user.id]['channel_id']
        channel = ctx.guild.get_channel(channel_id)
        await channel.set_permissions(user, overwrite=overwrite)

        # Create the embed object
        embed = discord.Embed(title="SLOT RELEASED", description=f"This slot has been released. You may now continue to trade with this user.", color=0x000000)
        embed.set_thumbnail(url="https://i.postimg.cc/25vXn6hS/static-4.png")

        # Send the message and embed to the channel
        new_embed = discord.Embed(title="SLOT RELEASED", description=f"Slot successfully released by {ctx.author.mention}", color=0x000000)
        new_embed.set_thumbnail(url="https://i.postimg.cc/25vXn6hS/static-4.png")

        # Send the message and new embed to the channel
        await ctx.send(embed=new_embed)
        await channel.send(embed=embed)


@client.command()
async def pingcount(ctx):
    user_id = ctx.author.id
    if user_id in user_slots:
        pings_left = user_slots[user_id].get('pings_left', 0)
        await ctx.send(f"You have {pings_left} pings left.")
    else:
        await ctx.send("You don't have a slot.")



# Assuming client is already defined somewhere in your bot code
@client.command()
async def uptime(ctx):
    current_time = int(time.time())  # Get current time
    uptime_seconds = current_time - start_time  # Calculate uptime using global start_time

    # Calculate days, hours, minutes, and seconds
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Construct the bot uptime string
    bot_uptime_string = ""
    if days:
        bot_uptime_string += f"{int(days)} day(s), "
    if hours:
        bot_uptime_string += f"{int(hours)} hour(s), "
    bot_uptime_string += f"{int(minutes)} minute(s) and {int(seconds)} second(s)"

    # Send bot uptime message
    await ctx.send(f"Bot has been up for: {bot_uptime_string}")

# Make sure the bot's start time is defined globally at the beginning of the script
start_time = time.time()  # Set start_time when the bot starts running

client.run(BOT_TOKEN)  # Ensure you have your BOT_TOKEN defined correctly