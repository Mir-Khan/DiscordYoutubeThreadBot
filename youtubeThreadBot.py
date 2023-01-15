# bot.py
import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
import youtubeLength as yt
# import pkg_resources

# print(pkg_resources.get_distribution("discord.py").version)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.message_content = True
discord.permissions

bot = commands.Bot(command_prefix='!', intents=intents)

# {"username": {"num_vids": int, "length_vids": int, "messages": [], "youtube_videos": []}
bot.thread_list = {}
# gets the most current thread created
bot.current_thread = None
# using these variables so these can be easily changes
bot.max_videos = 10
bot.max_length = 1800  # 30 minutes in seconds

# TODO
# Get list of videos from the latest thread when bot starts
# Allow user to remove videos from their current list
# Prevent users other than admin to submit messages in the parent channel

# main activity monitoring the thread and the channel which the thread is to be in
@bot.event
async def on_message(message):
    if hasattr(message.channel, "parent") and message.channel.id == bot.current_thread.id:
        if not yt.check_url(message.content) and message.author.id != bot.user.id:
            # video properties
            video_length = yt.url_to_time(message.content)
            video_title = message.embeds[0].title
            video_submitter = message.author
            # checks the thread list to make sure the user hasn't violated the submission rules
            if video_submitter in bot.thread_list and bot.thread_list[video_submitter]["num_vids"] < bot.max_videos and bot.thread_list[video_submitter]["length_vids"] < bot.max_length:
                bot.thread_list[video_submitter]["num_vids"] += 1
                bot.thread_list[video_submitter]["length_vids"] += video_length
                bot.thread_list[video_submitter]["messages"].append(message)
                bot.thread_list[video_submitter]["youtube_videos"].append(
                    video_title)
            elif video_submitter in bot.thread_list and ((bot.thread_list[video_submitter]["num_vids"] + 1) >= bot.max_videos or (bot.thread_list[video_submitter]["length_vids"] + video_length) >= bot.max_length):
                # if they have, their message is deleted and they're told to delete a video using the bot command
                await bot.current_thread.send(str(message.author.mention) + " Please delete a video using the bot command !delete [video title] before submitting another video")
                await message.delete()
            elif video_submitter not in bot.thread_list:
                # if its their first submission, they're added to the list
                bot.thread_list[video_submitter] = {"num_vids": 1, "length_vids": video_length, "messages": [
                    message], "youtube_videos": [video_title]}
        elif message.author.id != bot.user.id and yt.check_url(message.content) and not message.content.startswith(bot.command_prefix):
            await message.delete()
            await bot.current_thread.send(str(message.author.mention) + " Please submit a valid YouTube video.")
        await bot.process_commands(message)

# create thread command


@bot.command(name='thread')
@commands.has_any_role('nerd', 'admin')
async def create_thread(ctx, thread_name: str):
    try:
        bot.current_thread = await ctx.channel.create_thread(name=thread_name, type=discord.ChannelType.public_thread)
        await bot.current_thread.send("The rules are this!")
        await update_current_thread()
    except Exception as e:
        print(e)

# delete thread command


@bot.command(name="delete")
@commands.has_any_role('admin')
async def delete_thread(ctx, thread_name: str):
    try:
        current_channel_id = (discord.utils.get(
            ctx.guild.channels, name=str(ctx.channel))).id
        current_channel_threads = bot.get_channel(current_channel_id).threads
        deleted = False
        for thread in current_channel_threads:
            if thread.name == thread_name:
                deleted = True
                await thread.delete()
        if deleted:
            await ctx.send(thread_name + " was deleted!")
    except Exception as e:
        await ctx.send("There is no thread to delete!")
        print(e)

# update the most current thread to make sure its stored on startup


async def update_current_thread():
    try:
        channels = bot.get_all_channels()
        thread_channel = None
        if channels is not None:
            for channel in channels:
                if channel.name == 'threads':
                    thread_channel = channel
            bot.current_thread = thread_channel.threads[-1]
        print("got it")
    except Exception as e:
        await print(e)


@bot.event
async def on_ready():
    await update_current_thread()


########### DEBUG COMMANDS AND ERROR HANDLING #########

# update the most current thread manually
@bot.command(name='update')
@commands.has_any_role('admin')
async def update(ctx):
    try:
        current_channel_id = (discord.utils.get(
            ctx.guild.channels, name=str(ctx.channel))).id
        bot.current_thread = (bot.get_channel(current_channel_id).threads)[-1]
    except Exception as e:
        await print(e)

# check if the newest thread is stored


@bot.command(name="check")
@commands.has_any_role('admin')
async def check_thread(ctx):
    try:
        if bot.current_thread is None:
            await ctx.send("There is currently no thread stored")
        else:
            await ctx.send("The thread " + str(bot.current_thread.name) + " is stored")
    except Exception as e:
        print(e)

# error for the improper role


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')

bot.run(TOKEN)
