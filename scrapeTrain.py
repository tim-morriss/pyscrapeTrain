import re
import os
from io import BytesIO
import requests
import argparse
import unicodedata
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TPE1, TALB, APIC
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    # value = re.sub(r'[^\w\s-]', '', value.lower())
    value = re.sub(r'[^\w\s-]', '', value)
    return re.sub(r'[-\s]+', ' ', value).strip('-_')


# os agnostic home path
home_path = str(Path.home())

# cli argument for TrakTrain URL
parser = argparse.ArgumentParser(description="Script for downloading traktrain tracks.")
parser.add_argument('url', type=str, help="url for the traktrain profile")
args = parser.parse_args()
tt_url = args.url
artist = tt_url.rsplit('/', 1)[-1]  # artist name from end of url

# get TrakTrain page as beautiful soup object
r = requests.get(tt_url)
soup = BeautifulSoup(r.content, 'html.parser')
track_names = []
mp3_urls = []
artwork = []

# find all tracks on the page to get title and mp3-url
for d in soup.find_all("div", {"class": "js-profile-track"}):
    artwork.append(
        d.find(
            "img",
            attrs={"srcset": True}
        )['srcset'].split(', ')[1].split()[0]
    )
    track_names.append(
        slugify(d.find(
            "div",
            {"class": "title__name-tooltip"}
        ).text.strip('\n'), allow_unicode=True)
    )
    mp3_urls.append(d.find(attrs={"data-id": True})['data-id'])

# print(track_names)
# print(mp3_urls)
# print(artwork)

url_stub = ""

# find url stub for mp3s
scripts = soup.find_all("script", {"type": "text/javascript"})
for script in scripts:
    # print(stub)
    if "var AWS_BASE_URL" in script.text:
        s = script.text
        url_stub = re.search("(?P<url>https?://[^\s]+)\'", s).group("url")

# define where to save mp3s
dir_path = f"{home_path}/pyscrapeTrain/{artist}"

# make dir if not exists
if not os.path.exists(dir_path):
    os.makedirs(dir_path)

# use stub and mp3_urls to find all mp3 files on AWS and download them
# avoid stop stealing beats page by adding in origin and referer to request headers
print(f"Downloading {len(mp3_urls)} tracks by {artist}:")
for i in tqdm(range(len(mp3_urls))):
    url = url_stub + mp3_urls[i]
    req = Request(url)
    req.add_header('Origin', 'https://traktrain.com')
    req.add_header("Referer", "https://traktrain.com/")
    try:
        content = urlopen(req).read()
        mp3 = MP3(BytesIO(content))
        with open(f"{dir_path}/{track_names[i]}.mp3", 'wb') as f:
            f.write(content)
        if mp3.tags is None:
            mp3.tags = ID3()
        mp3.tags['TPE1'] = TPE1(encoding=3, text=artist)
        mp3.tags['TIT2'] = TALB(encoding=3, text=track_names[i])
        album_art = urlopen(artwork[i]).read()
        mp3.tags['APIC'] = APIC(
            encoding=3,
            mime='image/jpeg',
            type=3,
            desc=u'Cover',
            data=album_art
        )
        mp3.save(f"{dir_path}/{track_names[i]}.mp3")
    except HTTPError as e:
        # sometimes tracks 404 on AWS, this is a problem with TrakTrain not the script
        print(f"{e} \nfor track '{track_names[i]}' with url: {url}, continuing....")
        continue
