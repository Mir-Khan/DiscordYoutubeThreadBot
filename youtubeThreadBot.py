# bot.py
import os
import discord
from dotenv import load_dotenv
from discord.ext import commands, tasks
import youtubeLength as yt
import helperFunctions as hf
import time
# import pkg_resources

# print(pkg_resources.get_distribution("discord.py").version)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
ADMIN = os.getenv('ADMIN')
DEV = os.getenv('DEV')

intents = discord.Intents.default()
intents.message_content = True
discord.permissions

bot = commands.Bot(command_prefix='!', intents=intents)

# {"username": {"num_vids": int, "length_vids": int, "messages": [], "youtube_videos": [{title, length}]}
bot.thread_list = {}
# gets the most current thread created
bot.current_thread = None
# using these variables so these can be easily changes
bot.max_videos = 10
bot.max_length = 1800  # 30 minutes in seconds
bot.youtube_channel_name = "threads"


@bot.event
async def on_message(message):
    # this makes sure the bot only runs in the desired channel
    if message.channel.name != bot.youtube_channel_name and message.channel.name != bot.current_thread.name:
        return
    if message.channel.name == bot.youtube_channel_name and message.author.id != bot.user.id and not message.content.startswith(bot.command_prefix):
        isAdmin = False
        for role in message.author.roles:
            if role.name == ADMIN or role.name == DEV:
                isAdmin = True
        if not isAdmin:
            channel = message.channel
            mention = message.author.mention
            await message.delete()
            await channel.send(str(mention) + " Please either enter a command or link in the thread", delete_after=60)
    if hasattr(message.channel, "parent") and message.channel.id == bot.current_thread.id:
        isShort = True
        isVid = True
        if "shorts" in message.content:
            isShort = yt.check_short_url(message.content)
        else:
            isVid = yt.check_url(message.content)
        if "shorts" not in message.content and not isVid and message.author.id != bot.user.id:
            # video properties
            video_length = yt.url_to_time(message.content)
            video_title = yt.url_to_title(message.content)
            video_submitter = message.author.name
            # checks the thread list to make sure the user hasn't violated the submission rules
            if video_submitter in bot.thread_list and (bot.thread_list[video_submitter]["num_vids"] + 1) <= bot.max_videos and (bot.thread_list[video_submitter]["length_vids"] + video_length) <= bot.max_length:
                hf.video_list_exists(
                    bot.thread_list, video_length, video_title, video_submitter, message)
            elif video_submitter in bot.thread_list and ((bot.thread_list[video_submitter]["num_vids"] + 1) > bot.max_videos or (bot.thread_list[video_submitter]["length_vids"] + video_length) > bot.max_length):
                # if they have, their message is deleted and they're told to delete a video using the bot command
                reason = hf.reason_gen(bot.thread_list[video_submitter]["num_vids"] + 1,
                                       bot.thread_list[video_submitter]["length_vids"] + video_length, bot.max_videos, bot.max_length)
                await message.delete()
                await bot.current_thread.send(str(message.author.mention) + 'Please delete a video/short using the bot command **!delete "title"** before submitting another video. ' + reason, delete_after=60)
            elif video_submitter not in bot.thread_list:
                # if its their first submission, they're added to the list
                hf.video_list_new(
                    bot.thread_list, video_length, video_title, video_submitter, message)
        elif message.author.id != bot.user.id and "shorts" in message.content and not isShort:
            # this section deals with youtube shorts
            short_info = yt.get_short_info(message.content)
            video_length = short_info.length
            video_title = short_info.title
            video_submitter = message.author.name
            if video_submitter in bot.thread_list and (bot.thread_list[video_submitter]["num_vids"] + 1) <= bot.max_videos and (bot.thread_list[video_submitter]["length_vids"] + video_length) <= bot.max_length:
                hf.video_list_exists(
                    bot.thread_list, video_length, video_title, video_submitter, message)
            elif video_submitter in bot.thread_list and ((bot.thread_list[video_submitter]["num_vids"] + 1) > bot.max_videos or (bot.thread_list[video_submitter]["length_vids"] + video_length) > bot.max_length):
                # if they have, their message is deleted and they're told to delete a video using the bot command
                reason = hf.reason_gen(bot.thread_list[video_submitter]["num_vids"] + 1,
                                       bot.thread_list[video_submitter]["length_vids"] + video_length, bot.max_videos, bot.max_length)
                await message.delete()
                await bot.current_thread.send(str(message.author.mention) + 'Please delete a video/short using the bot command **!delete "title"** before submitting another video. ' + reason, delete_after=60)
            elif video_submitter not in bot.thread_list:
                # if its their first submission, they're added to the list
                hf.video_list_new(
                    bot.thread_list, video_length, video_title, video_submitter, message)
        elif message.author.id != bot.user.id and "shorts" not in message.content and not message.content.startswith(bot.command_prefix) and isVid:
            # if not a valid youtube video, message is deleted and user is notified
            await message.delete()
            await bot.current_thread.send(str(message.author.mention) + " Please submit a valid YouTube video.", delete_after=60)
        elif message.author.id != bot.user.id and "shorts" in message.content and not message.content.startswith(bot.command_prefix) and isShort:
            # if not a valid youtube video, message is deleted and user is notified
            await message.delete()
            await bot.current_thread.send(str(message.author.mention) + " Please submit a valid YouTube short.", delete_after=60)
    await bot.process_commands(message)

# create thread command


@bot.command(name='make')
@commands.has_any_role(DEV, ADMIN)
async def create_thread(ctx, thread_name: str):
    try:
        bot.current_thread = await ctx.channel.create_thread(name=thread_name, type=discord.ChannelType.public_thread)
        await bot.current_thread.send("``The rules are this!``", delete_after=60)
        await update_current_thread()
    except Exception as e:
        print(e)

# delete thread command


@bot.command(name="delete-thread")
@commands.has_any_role(DEV, ADMIN)
async def delete_thread(ctx, thread_name: str):
    try:
        current_channel_id = (discord.utils.get(
            ctx.guild.channels, name=str(ctx.channel))).id
        current_channel_threads = bot.get_channel(current_channel_id).threads
        deleted = False
        for thread in current_channel_threads:
            if thread.name == thread_name:
                bot.thread_list = {}
                bot.current_thread = None
                deleted = True
                await thread.delete()
        if deleted:
            await ctx.send("``" + thread_name + " was deleted!``", delete_after=60)
    except Exception as e:
        await ctx.send("``There is no thread to delete!``", delete_after=60)
        print(e)


# delete video commands

@bot.command(name="delete")
async def delete_video_name(ctx, video_name):
    try:
        if bot.thread_list:
            original_number = bot.thread_list[ctx.author.name]["num_vids"]
            if ctx.author.name in bot.thread_list:
                index = -1
                for video in reversed(bot.thread_list[ctx.author.name]["youtube_videos"]):
                    increase = await hf.delete_video(bot.thread_list, "title", video, ctx.author.name, index, video_name)
                    if increase:
                        index -= 1
        if original_number != bot.thread_list[ctx.author.name]["num_vids"]:
            await ctx.send(str(ctx.author.mention) + " Video(s) with title: " + video_name + " was deleted!", delete_after=60)
        else:
            await ctx.send(str(ctx.author.mention) + " Video(s) with title: " + video_name + " was not found!", delete_after=60)

    except Exception as e:
        print(e)


@bot.command(name="check-videos")
async def check_videos(ctx):
    try:
        user = ctx.author.name
        inList = False
        endString = ""
        for thread_user in bot.thread_list:
            if user == thread_user:
                inList = True
                num_vids = thread_user['num_vids']
                length_vids = time.strftime(
                    "%M:%S", time.gmtime(thread_user['length_vids']))
                youtube_videos = []
                for videos in thread_user['youtube_videos']:
                    youtube_videos.append(videos.title)
                youtube_videos = ', '.join(youtube_videos)
                endString = "``You have " + \
                    str(num_vids) + " videos and " + \
                    length_vids + " of content``"
        if not inList:
            await ctx.send("``You don't have any videos in the thread!``", delete_after=60)
            return
        else:
            await ctx.send(endString, delete_after=60)

    except Exception as e:
        print(e)

# command to notify user of rules


@bot.command(name="rules")
async def rules(ctx):
    try:
        user = ctx.author
        rules = "\n>>> **__RULES:__**\n1. No more than 10 videos\n2.No more than a total of 30 minutes of content\n3.Only message in the latest thread indicated in the sidebar of the left, **BELOW** the channel name!"
        await ctx.send(user.mention + rules, delete_after=60)
    except Exception as e:
        print(e)

# update the most current thread to make sure its stored on startup


async def update_current_thread():
    try:
        channels = bot.get_all_channels()
        thread_channel = None
        if channels is not None:
            for channel in channels:
                if channel.name == bot.youtube_channel_name:
                    thread_channel = channel
            if thread_channel.threads:
                bot.current_thread = thread_channel.threads[-1]
        print("got it")
    except Exception as e:
        await print(e)

# makes sure on start up the bot is working properly


async def get_thread_messages():
    try:
        if bot.current_thread is not None:
            async for message in bot.current_thread.history(limit=3000):
                if ("youtu.be" in message.content or "youtube.com" in message.content) and "shorts" not in message.content and not yt.check_url(message.content):
                    video_submitter = message.author.name
                    video_title = yt.url_to_title(message.content)
                    video_length = yt.url_to_time(message.content)
                    if video_submitter in bot.thread_list and (bot.thread_list[video_submitter]["num_vids"] + 1) <= bot.max_videos and (bot.thread_list[video_submitter]["length_vids"] + video_length) <= bot.max_length:
                        hf.video_list_exists_on_start(
                            bot.thread_list, video_length, video_title, video_submitter, message)
                    elif video_submitter in bot.thread_list and ((bot.thread_list[video_submitter]["num_vids"] + 1) > bot.max_videos or (bot.thread_list[video_submitter]["length_vids"] + video_length) >= bot.max_length):
                        await message.delete()
                    else:
                        hf.video_list_new(
                            bot.thread_list, video_length, video_title, video_submitter, message)
                elif "shorts" in message.content and not yt.check_short_url(message.content):
                    short_info = yt.get_short_info(message.content)
                    video_submitter = message.author.name
                    video_title = short_info.title
                    video_length = short_info.length
                    if video_submitter in bot.thread_list and ((bot.thread_list[video_submitter]["num_vids"] + 1) <= bot.max_videos or (bot.thread_list[video_submitter]["length_vids"] + video_length) <= bot.max_length):
                        hf.video_list_exists_on_start(
                            bot.thread_list, video_length, video_title, video_submitter, message)
                    elif video_submitter in bot.thread_list and ((bot.thread_list[video_submitter]["num_vids"] + 1) > bot.max_videos or (bot.thread_list[video_submitter]["length_vids"] + video_length) >= bot.max_length):
                        await message.delete()
                    else:
                        hf.video_list_new(
                            bot.thread_list, video_length, video_title, video_submitter, message)
    except Exception as e:
        print(e)

# on bot start


@bot.event
async def on_ready():
    update_list_task.start()


# daily task to check the thread list

@tasks.loop(hours=24)
async def update_list_task():
    await update_current_thread()
    await get_thread_messages()

########### DEBUG COMMANDS AND ERROR HANDLING #########

# prints the thread list to console


@bot.command(name="thread_list")
@commands.has_any_role(DEV, ADMIN)
async def check_list(ctx):
    print(bot.thread_list)

# update the most current thread manually


@bot.command(name='update')
@commands.has_any_role(DEV, ADMIN)
async def update(ctx):
    try:
        current_channel_id = (discord.utils.get(
            ctx.guild.channels, name=str(ctx.channel))).id
        bot.current_thread = (bot.get_channel(current_channel_id).threads)[-1]
    except Exception as e:
        await print(e)

# check if the newest thread is stored


@bot.command(name="check-queue")
@commands.has_any_role(DEV, ADMIN)
async def check_thread(ctx):
    try:
        if bot.current_thread is None:
            await ctx.send("``There is currently no thread stored``", delete_after=60)
        else:
            await ctx.send("``The thread " + str(bot.current_thread.name) + " is stored``", delete_after=60)
    except Exception as e:
        print(e)

# error for the improper role


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('``You do not have the correct role for this command.``', delete_after=60)

bot.run(TOKEN)
