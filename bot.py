import os
import discord
from dotenv import load_dotenv
from discord.ext import commands, tasks
import youtubeLength as yt
import helperFunctions as hf
import time
import sys

# environment variables loaded here
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
ADMIN = os.getenv('ADMIN')
DEV = os.getenv('DEV')
THREAD_CHANNEL = os.getenv('THREAD_CHANNEL')
MAX_TOTAL = os.getenv('MAX_TOTAL')
MAX_VIDEOS = os.getenv('MAX_VIDEOS')
MAX_INDIVIDUAL_VIDEO_LENGTH = os.getenv('MAX_INDIVIDUAL_VIDEO_LENGTH')

intents = discord.Intents.default()
intents.message_content = True
discord.permissions

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# {"username": {"num_vids": int, "length_vids": int, "messages": [], "youtube_videos": [{title, length}]}
bot.thread_list = {}
# gets the most current thread created
bot.current_thread = None
# name of the channel with the threads
bot.youtube_channel_name = THREAD_CHANNEL
# admin/dev command list
bot.dev_commands = ["update", "check-queue", "thread_list",
                    "delete-thread", "make", "rename", "help-admin", "rules-pin", "help-pin", "daily"]

# TODO
# NEED TO TEST

####################################################################### EVENTS #######################################################################

@bot.event
async def on_message(message):
    # avoids catching debug dms
    if not message.guild:
        return
    # this catches the initial message in a thread by the bot to pin it
    if message.content == "Please place your videos here! Max of 10 videos, total content should **NOT** exceed 30 minutes, and videos should not be longer than 15 minutes":
        await message.pin()
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
            await channel.send(str(mention) + " How about you read the rules you bozo 🙂", delete_after=20)
    if hasattr(message.channel, "parent") and message.channel.id == bot.current_thread.id:
        # checking if a link is a short or video
        isNotShort = True
        isNotVid = True
        if "shorts" in message.content:
            isNotShort = yt.check_url(message.content)
        else:
            isNotVid = yt.check_url(message.content)
        if isNotShort and not isNotVid and message.author.id != bot.user.id:
            # videos dealt with here
            # video properties
            video_length = yt.url_to_time(message.content)
            video_title = yt.url_to_title(message.content)
            video_submitter = message.author.id
            
            # checks the thread list to make sure the user hasn't violated the submission rules
            if video_submitter in bot.thread_list.keys() and (bot.thread_list[video_submitter]["num_vids"] + 1) <= bot.max_videos and (bot.thread_list[video_submitter]["length_vids"] + video_length) <= bot.max_length and video_length < bot.max_individual_video_length:
                hf.video_list_exists(
                    bot.thread_list, video_length, video_title, video_submitter, message)
            elif video_submitter in bot.thread_list.keys() and ((bot.thread_list[video_submitter]["num_vids"] + 1) > bot.max_videos or (bot.thread_list[video_submitter]["length_vids"] + video_length) > bot.max_length) or video_length > bot.max_individual_video_length:
                # if they have, their message is deleted and they're told to delete a video using the bot command
                reason = hf.reason_gen(bot.thread_list[video_submitter]["num_vids"] + 1,
                                       bot.thread_list[video_submitter]["length_vids"] + video_length, bot.max_videos, bot.max_length, video_length, bot.max_individual_video_length)
                await message.delete()
                await bot.current_thread.send(str(message.author.mention) + 'Please delete a video/short using the bot command **!delete title** before submitting another video. ' + reason, delete_after=60)
            elif video_submitter not in bot.thread_list.keys() and video_length < bot.max_individual_video_length:
                # if its their first submission, they're added to the list
                hf.video_list_new(
                    bot.thread_list, video_length, video_title, video_submitter, message)
            elif video_submitter not in bot.thread_list and video_length > bot.max_individual_video_length:
                await message.delete()
                await bot.current_thread.send(str(message.author.mention) + ' Please submit a video of length 15 minutes or less.', delete_after=60)
        elif message.author.id != bot.user.id and not isNotShort:
            # this section deals with youtube shorts
            short_info = yt.get_short_info(message.content)
            video_length = short_info.length
            video_title = short_info.title
            video_submitter = message.author.id
            # checks the thread list to make sure the user hasn't violated the submission rules
            if video_submitter in bot.thread_list.keys() and (bot.thread_list[video_submitter]["num_vids"] + 1) <= bot.max_videos and (bot.thread_list[video_submitter]["length_vids"] + video_length) <= bot.max_length and video_length < bot.max_individual_video_length:
                hf.video_list_exists(
                    bot.thread_list, video_length, video_title, video_submitter, message)
            elif video_submitter in bot.thread_list.keys() and ((bot.thread_list[video_submitter]["num_vids"] + 1) > bot.max_videos or (bot.thread_list[video_submitter]["length_vids"] + video_length) > bot.max_length) or video_length > bot.max_individual_video_length:
                # if they have, their message is deleted and they're told to delete a video using the bot command
                reason = hf.reason_gen(bot.thread_list[video_submitter]["num_vids"] + 1,
                                       bot.thread_list[video_submitter]["length_vids"] + video_length, bot.max_videos, bot.max_length, video_length, bot.max_individual_video_length)
                await message.delete()
                await bot.current_thread.send(str(message.author.mention) + 'Please delete a video/short using the bot command **!delete title** before submitting another video. ' + reason, delete_after=60)
            elif video_submitter not in bot.thread_list.keys() and video_length < bot.max_individual_video_length:
                # if its their first submission, they're added to the list
                hf.video_list_new(
                    bot.thread_list, video_length, video_title, video_submitter, message)
            elif video_submitter not in bot.thread_list.keys() and video_length > bot.max_individual_video_length:
                await message.delete()
                await bot.current_thread.send(str(message.author.mention) + ' Please submit a video of length 15 minutes or less.', delete_after=60)
        elif message.author.id != bot.user.id and isNotShort and not message.content.startswith(bot.command_prefix) and not isNotVid:
            # if not a valid youtube video, message is deleted and user is notified
            await message.delete()
            await bot.current_thread.send(str(message.author.mention) + " Please submit a valid YouTube video.", delete_after=60)
        elif message.author.id != bot.user.id and not isNotShort and not message.content.startswith(bot.command_prefix) and isNotVid:
            # if not a valid youtube video, message is deleted and user is notified
            await message.delete()
            await bot.current_thread.send(str(message.author.mention) + " Please submit a valid YouTube short.", delete_after=60)
    await bot.process_commands(message)
    # deletes the command after a few seconds to ensure the channel/thread is cleaned up
    if message.content.startswith("!"):
        await message.delete(delay=20)


####################################################################### COMMANDS #######################################################################

#################### COMMANDS FOR EVERYONE ####################

# delete video commands

@bot.command(name="delete-name", description="Deletes all videos with the matching title")
async def delete_video_name(ctx, *, video_name: str):
    try:
        if bot.thread_list:
            original_number = bot.thread_list[ctx.author.id]["num_vids"]
            if ctx.author.id in bot.thread_list:
                # note the list goes in reverse to go from the top of the channel and the index is -1 to ensure we don't lose our place after deleting
                index = -1
                for video in reversed(bot.thread_list[ctx.author.id]["youtube_videos"]):
                    increase = await hf.delete_video_by_name(bot.thread_list, "title", video, ctx.author.id, index, video_name)
                    if increase:
                        index -= 1
        if original_number != bot.thread_list[ctx.author.id]["num_vids"]:
            await ctx.send(str(ctx.author.mention) + " Video(s) with title: " + video_name + " was deleted!", delete_after=60)
        else:
            await ctx.send(str(ctx.author.mention) + " Video(s) with title: " + video_name + " was not found!", delete_after=60)

    except Exception as e:
        await ctx.send(str(ctx.author.mention) + " something went wrong! Make sure you put in an appropriate name :kermitW: . Type !help if you aren't sure.", delete_after=60)
        print(e)

@bot.command(name="delete-num", description="Deletes videos in the list of videos with the matching index (example, if you want to delete your first video, use !delete-num 1)")
async def delete_video_num(ctx, *, video_index: str):
    try:
        if bot.thread_list:
            if ctx.author.id in bot.thread_list:
                index = int(video_index) - 1
                original_number = bot.thread_list[ctx.author.id]["num_vids"]
                video_name = bot.thread_list[ctx.author.id]["youtube_videos"][index]["title"]
                await hf.delete_video_by_num(bot.thread_list, ctx.author.id, index)
            if original_number != bot.thread_list[ctx.author.id]["num_vids"]:
                await ctx.send(str(ctx.author.mention) + " Video(s) with title: " + video_name + " was deleted!", delete_after=60)
    except Exception as e:
        await ctx.send(str(ctx.author.mention) + " something went wrong! Make sure you put in an appropriate index :kermitW: . Type !help if you aren't sure what that means.", delete_after=60)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)

# command to check how much content a user has in a thread


@bot.command(name="check-videos", description="Checks how many videos you have in queue, what videos you entered, and the total length of the videos")
async def check_videos(ctx):
    try:
        user = ctx.author.id
        inList = False
        endString = ""
        for thread_user in bot.thread_list:
            if user == thread_user:
                inList = True
                num_vids = bot.thread_list[thread_user]['num_vids']
                length_vids = time.strftime(
                    "%M:%S", time.gmtime(bot.thread_list[thread_user]['length_vids']))
                youtube_videos = []
                for videos in bot.thread_list[thread_user]['youtube_videos']:
                    youtube_videos.append(videos["title"])
                endString = "``You have " + \
                    str(num_vids) + " videos and " + \
                    length_vids + " of content. \n Your videos are:\n"
                video_number = 1
                for video in youtube_videos:
                    endString += str(video_number) + ". " + str(video) + "\n"
                    video_number += 1
                endString += "``"
            if inList:
                break
        if not inList or bot.thread_list[ctx.author.id]["num_vids"] == 0:
            await ctx.send("``You don't have any videos in the thread!``", delete_after=60)
            return
        else:
            await ctx.send(endString, delete_after=60)

    except Exception as e:
        print(e)

# command to notify user of rules


@bot.command(name="rules", description="Shows the submission rules")
async def rules(ctx):
    try:
        user = ctx.author
        rules = "\n>>> **__RULES:__**\n1. No more than 10 videos\n2.No more than a total of 30 minutes of content\n3.Only message in the latest thread!"
        await ctx.send(user.mention + rules, delete_after=60)
    except Exception as e:
        print(e)


@bot.command(name="rules-pin", description="Shows the submission rules")
@commands.has_any_role(DEV, ADMIN)
async def rules(ctx):
    try:
        rules = "\n>>> **__RULES:__**\n1. No more than 10 videos\n2.No more than a total of 30 minutes of content\n3.Only message in the latest thread!\n4.Use !help to see the list of commands available"
        await ctx.send(rules)
    except Exception as e:
        print(e)

# help commands

@bot.command(name="help", description="Shows description of all commands")
async def help(ctx):
    try:
        endString = await hf.help_string(bot.commands, bot.dev_commands, False)
        await ctx.send(endString, delete_after=60)
    except Exception as e:
        print(e)

#pin command for help

@bot.command(name="help-pin", description="Help command to help pin the commands for users")
@commands.has_any_role(DEV, ADMIN)
async def help(ctx):
    try:
        endString = await hf.help_string(bot.commands, bot.dev_commands, False)
        await ctx.send(endString)
    except Exception as e:
        print(e)

#  for dev commands


@bot.command(name="help-admin", description="Shows admin/dev commands")
@commands.has_any_role(DEV, ADMIN)
async def help_debug(ctx):
    try:
        endString = await hf.help_string(bot.commands, bot.dev_commands, True)
        dms = await ctx.author.create_dm()
        await dms.send(endString)
    except Exception as e:
        print(e)

#################### COMMANDS FOR ADMINS AND DEVS ####################

# create thread command


@bot.command(name='make', description='Makes a thread with the specified name')
@commands.has_any_role(DEV, ADMIN)
async def create_thread(ctx, thread_name: str):
    try:
        bot.current_thread = await ctx.channel.create_thread(name=thread_name, type=discord.ChannelType.public_thread)
        await bot.current_thread.send("Please place your videos here! Max of 10 videos, total content should **NOT** exceed 30 minutes, and videos should not be longer than 15 minutes")
        await update_current_thread()
    except Exception as e:
        print(e)

# delete thread command


@bot.command(name="delete-thread", description="Deletes a thread with the specified name")
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

# rename thread command


@bot.command(name="rename", description="Renames a thread with the specified name")
@commands.has_any_role(ADMIN, DEV)
async def rename_thread(ctx, *, new_name: str):
    try:
        channels = bot.get_all_channels()
        thread_channel = None
        if channels is not None:
            for channel in channels:
                if channel.name == bot.youtube_channel_name:
                    thread_channel = channel
                    if thread_channel.threads:
                        await thread_channel.threads[-1].edit(name=new_name, reason="bot rename thread command ran by " + ctx.author.name)
                        bot.current_thread = thread_channel.threads[-1]
                    else:
                        await ctx.send("There is no thread to edit!", delete_after=60)
    except Exception as e:
        print(e)

####################################################################### TASKS AND STARTUP #######################################################################

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
                    video_submitter = message.author.id
                    video_title = yt.url_to_title(message.content)
                    video_length = yt.url_to_time(message.content)
                    if video_submitter in bot.thread_list.keys() and (bot.thread_list[video_submitter]["num_vids"] + 1) <= bot.max_videos and (bot.thread_list[video_submitter]["length_vids"] + video_length) <= bot.max_length:
                        hf.video_list_exists_on_start(
                            bot.thread_list, video_length, video_title, video_submitter, message)
                    elif video_submitter not in bot.thread_list.keys() and video_length < bot.max_individual_video_length:
                        hf.video_list_new(
                            bot.thread_list, video_length, video_title, video_submitter, message)
                elif "shorts" in message.content and not yt.check_url(message.content):
                    short_info = yt.get_short_info(message.content)
                    video_submitter = message.author.id
                    video_title = short_info.title
                    video_length = short_info.length
                    if video_submitter in bot.thread_list.keys() and ((bot.thread_list[video_submitter]["num_vids"] + 1) <= bot.max_videos and (bot.thread_list[video_submitter]["length_vids"] + video_length) <= bot.max_length):
                        hf.video_list_exists_on_start(
                            bot.thread_list, video_length, video_title, video_submitter, message)
                    elif video_submitter not in bot.thread_list.keys() and video_length < bot.max_individual_video_length:
                        hf.video_list_new(
                            bot.thread_list, video_length, video_title, video_submitter, message)
    except Exception as e:
        print(e)

# makes sure the thread has the proper amount of messages and time-lengths

async def delete_thread_messages():
    try:
        if bot.current_thread is not None:
            for user in bot.thread_list:
                if bot.thread_list[user]['length_vids'] > bot.max_length or bot.thread_list[user]['num_vids'] > bot.max_videos:
                    bot.thread_list[user]['length_vids'] -= bot.thread_list[user]['youtube_videos'][-1].length
                    bot.thread_list[user]['num_vids'] -= 1
                    video_title = bot.thread_list[user]['youtube_videos'][-1].title
                    message_copy = []
                    for message in reversed(bot.thread_list[user]['messages']):
                        if ("youtu.be" in message.content or "youtube.com" in message.content or "/shorts/" in message.content) and (yt.url_to_title(message.content) == video_title):
                            await bot.current_thread.send(str(message.author.mention) + " Your video titled " + str(video_title) + " was deleted after checking the thread. If this wasn't right, please message Rykers and let him know! (Another bug :PepeHands:)")
                            await message.delete()
                        else:
                            message_copy.append(message)
                    bot.thread_list[user]['messages'] = message_copy
                    bot.thread_list[user]['youtube_videos'] = bot.thread_list[user]['youtube_videos'][:-1]
    except Exception as e:
        print(e)

async def set_globals():
    try:
        bot.max_videos = int(MAX_VIDEOS)
        bot.max_length = int(MAX_TOTAL)
        bot.max_individual_video_length = int(MAX_INDIVIDUAL_VIDEO_LENGTH)
    except:
        # resort to defaults if not able to retreive environment
        bot.max_videos = 10
        bot.max_length = 1860
        bot.max_individual_video_length = 960
# on bot start


@bot.event
async def on_ready():
    update_list_task.start()


# daily task to check the thread list

@tasks.loop(hours=24)
async def update_list_task():
    await set_globals()
    await update_current_thread()
    await get_thread_messages()
    await delete_thread_messages()

####################################################################### DEBUG COMMANDS AND ERROR HANDLING #######################################################################

# prints the thread list to console


@bot.command(name="thread_list", description="Prints the thread list to console")
@commands.has_any_role(DEV, ADMIN)
async def check_list(ctx):
    print(bot.thread_list)

# update the most current thread manually


@bot.command(name='update', description="Updates what the most current thread is")
@commands.has_any_role(DEV, ADMIN)
async def update(ctx):
    try:
        await set_globals()
        await update_current_thread()
        await get_thread_messages()
        await delete_thread_messages()
    except Exception as e:
        await print(e)

# check if the newest thread is stored


@bot.command(name="check-queue", description="Checks the most current thread")
@commands.has_any_role(DEV, ADMIN)
async def check_thread(ctx):
    try:
        if bot.current_thread is None:
            await ctx.send("``There is currently no thread stored``", delete_after=60)
        else:
            await ctx.send("``The thread " + str(bot.current_thread.name) + " is stored``", delete_after=60)
    except Exception as e:
        print(e)

# run the daily run commands

@bot.command(name="daily", description="runs the daily tasks")
@commands.has_any_role(DEV, ADMIN)
async def run_dailies(ctx):
    try:
        await update_list_task()
        await ctx.message.delete()
    except Exception as e:
        print(e)

# error for the improper role


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send(str(ctx.author.mention) + " - HEY!! KNOCK IT OFF BOZO! YOU CAN'T USE THIS COMMAND!!", delete_after=10)

bot.run(TOKEN)
