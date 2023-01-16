def reason_gen(number_vids, length, max_videos, max_length):
    isNumber = False
    isLength = False
    if (number_vids) > max_videos:
        isNumber = True
    if (length) > max_length:
        isLength = True
    reason = None
    if isLength and isNumber:
        reason = "**You have 10 videos and over 30 minutes of content with this submission.**"
    elif isNumber:
        reason = "**You have 10 videos already.**"
    elif isLength:
        reason = "**You have over 30 minutes of content with this submission.**"
    return reason

# if the author is already in the list this function is used


def video_list_exists(original_list, video_length, video_title, video_submitter, message):
    original_list[video_submitter]["num_vids"] += 1
    original_list[video_submitter]["length_vids"] += video_length
    original_list[video_submitter]["messages"].append(message)
    original_list[video_submitter]["youtube_videos"].append(
        {"title": video_title, "length": video_length, "url": message.content})


def video_list_exists_on_start(original_list, video_length, video_title, video_submitter, message):
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
async def delete_video(original_list, criteria, video, user, index, criteria_given):
    if video[criteria] == criteria_given:
        original_list[user]["num_vids"] -= 1
        original_list[user]["length_vids"] -= video["length"]
        del original_list[user]["youtube_videos"][index]
        await original_list[user]["messages"][index].delete()
        del original_list[user]["messages"][index]
        return False
    else:
        return True
