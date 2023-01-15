import pafy
import requests

def url_to_time(url):
    return (pafy.new(url)).length

def check_if_length_limit(seconds):
    return bool(seconds < 1800)

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