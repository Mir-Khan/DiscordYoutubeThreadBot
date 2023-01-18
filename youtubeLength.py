import os
from dotenv import load_dotenv
import requests
from pytube import YouTube


def url_to_time(url):
    return YouTube(url).length


def url_to_title(url):
    return YouTube(url).title


def get_short_info(url):
    try:
        return YouTube(url)
    except Exception as e:
        print(e)

# if true, not a valid url


def check_url(url):
    try:
        if "https://" not in url:
            return True
        else:
            r = requests.get(url)
            return "Video unavailable" in r.text
    except Exception as e:
        print(e)
