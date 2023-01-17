import os
from dotenv import load_dotenv
import pafy
import requests

load_dotenv()
pafy.set_api_key(os.getenv('YOUTUBE_API'))


def url_to_time(url):
    return (pafy.new(url)).length

def url_to_title(url):
    return (pafy.new(url)).title

def get_short_info(url):
    # add 7 to get to start of id
    shorts_slash = url.find("shorts/") + 7
    # video id is always 11 characters in length
    short_id = url[shorts_slash:shorts_slash + 11]
    return pafy.new(short_id)

# if true, not a valid url


def check_url(url):
    try:
        if "https://" not in url:
            return True
        r = requests.get(url)
        return "Video unavailable" in r.text
    except Exception as e:
        print(e)
        return True

def check_short_url(url):
    try:
        if "https://" not in url:
            return True
        else:
            shorts_slash = url.find("shorts/") + 7
            short_id = url[shorts_slash: shorts_slash + 11]
            pafy.new(short_id)
            return False
    except Exception as e:
        if "ERROR: Video unavailable".lower() == str(e).lower():
            return True
