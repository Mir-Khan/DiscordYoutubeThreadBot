import os
import sys
import re
from dotenv import load_dotenv
import requests
from pytube import YouTube


def url_to_time(url):
    try:
        text_split = url.split()
        final_url = ""
        for text in text_split:
            if check_link(text):
                final_url = text
        return YouTube(url=str(final_url)).length
    except:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)


def url_to_title(url):
    try:
        text_split = url.split()
        final_url = ""
        for text in text_split:
            if check_link(text):
                final_url = text
        return YouTube(url=str(final_url)).title
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return "Title not found"


def check_link(url):
    if re.search("youtube.com", url) or re.search("youtu.be", url):
        return True
    else:
        return False


def get_short_info(url):
    try:
        text_split = url.split()
        final_url = ""
        for text in text_split:
            if check_link(text):
                final_url = text
        return YouTube(final_url)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)

# if true, not a valid url


def check_url(url):
    try:
        if "https://" not in url:
            return True
        else:
            r = requests.get(url)
            return "Video unavailable" in r.text
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
