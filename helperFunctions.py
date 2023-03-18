import sys
import os
def reason_gen(number_vids, length, max_videos, max_length, video_length, max_video_length):
    isNumber = False
    isLength = False
    isVideo = False
    if (number_vids) > max_videos:
        isNumber = True
    if (length) > max_length:
        isLength = True
    if video_length > max_video_length:
        isVideo = True
    reason = None
    if isLength and isNumber:
        reason = "**You have 10 videos and over 45 minutes of content with this submission.**"
    elif isNumber:
        reason = "**You have 10 videos already.**"
    elif isLength and not isVideo:
        reason = "**You have over 45 minutes of content with this submission.**"
    elif isVideo:
        reason = "**Your video is longer than 10 minutes.**"
    return reason

# if the author is already in the list this function is used


def video_list_exists(original_list, video_length, video_title, video_submitter, message):
    try:
        videoExists = False
        for video in original_list[video_submitter]["youtube_videos"]:
            if video_title == video["title"]:
                videoExists = True
        if(not videoExists):
            original_list[video_submitter]["num_vids"] += 1
            original_list[video_submitter]["length_vids"] += video_length
            original_list[video_submitter]["messages"].append(message)
            original_list[video_submitter]["youtube_videos"].append(
                {"title": video_title, "length": video_length, "url": message.content})
    except:
        video_list_new(original_list, video_length, video_title, video_submitter, message)


def video_list_exists_on_start(original_list, video_length, video_title, video_submitter, message):
    videoExists = False
    for video in original_list[video_submitter]["youtube_videos"]:
        if video_title == video["title"]:
            videoExists = True
    if(not videoExists):
        original_list[video_submitter]["num_vids"] += 1
        original_list[video_submitter]["length_vids"] += video_length
        original_list[video_submitter]["messages"].insert(0, message)
        original_list[video_submitter]["youtube_videos"].insert(0,
                                                                {"title": video_title, "length": video_length, "url": message.content})

# if the author isnt already in the list


def video_list_new(original_list, video_length, video_title, video_submitter, message):
    original_list[video_submitter] = {"num_vids": 1, "length_vids": video_length, "messages": [
        message], "youtube_videos": [{"title": video_title, "length": video_length, "url": message.content}]}


# deletes videos and reflects the change in the thread list
async def delete_video_by_name(original_list, current_video_name, video, user, index, video_name):
    try:
        if video[current_video_name] == video_name:
            original_list[user]["num_vids"] -= 1
            original_list[user]["length_vids"] -= video["length"]
            del original_list[user]["youtube_videos"][index]
            await original_list[user]["messages"][index].delete()
            del original_list[user]["messages"][index]
            return False
        else:
            return True
    except:
        return True

async def delete_video_by_num(original_list, user, index):
    try:
        original_list[user]["num_vids"] -= 1
        original_list[user]["length_vids"] -= original_list[user]["youtube_videos"][index]["length"]
        original_list[user]["youtube_videos"].pop(index)
        await original_list[user]["messages"][index].delete()
        original_list[user]["messages"].pop(index)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)

async def help_string(commands, dev_commands, admin):
    command_names_and_params = []
    command_descriptions = []
    for command in commands:
        if command.name in dev_commands and admin:
            command_names_and_params.append(
                {"name": command.name, "params": command.signature})
            command_descriptions.append(command.description)
        elif command.name not in dev_commands and not admin:
            command_names_and_params.append(
                {"name": command.name, "params": command.signature})
            command_descriptions.append(command.description)
    endString = ">>> "
    if admin:
        endString += "DEBUG COMMANDS\n"
    index = 0
    while index < len(command_names_and_params):
        paramString = ""
        if str(command_names_and_params[index]["params"]) != "":
            paramString = "__*" + \
                str(command_names_and_params[index]["params"]) + "*__"
        endString += "**" + str(command_names_and_params[index]["name"]) + \
            "** " + paramString + " - " + \
            str(command_descriptions[index]) + "\n"
        index += 1
    return endString
