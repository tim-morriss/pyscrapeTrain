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
from mutagen.id3 import ID3, TPE1, TIT2, TALB, APIC
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


# cli argument for TrakTrain URL
parser = argparse.ArgumentParser(description="Script for downloading traktrain tracks.")
parser.add_argument(
    'url',
    type=str,
    help="url for the traktrain profile")
parser.add_argument(
    '-d',
    '--dir',
    dest='directory',
    default=None,
    type=str,
    help="directory to save mp3s to. format: <dir>/pyscrapeTrain/<artist>"
)
parser.add_argument(
    '-a',
    '--album',
    dest='album',
    default=None,
    type=str,
    help="Custom name for ID3 tags, for sorting"
)

args = parser.parse_args()
tt_url = args.url
# artist = tt_url.rsplit('/', 1)[-1]  # artist name from end of url
if not args.directory:
    # os agnostic home path
    output_dir = str(Path.home())
else:
    output_dir = args.directory
# define where to save mp3s
ALBUM = args.album

# get TrakTrain page as beautiful soup object
r = requests.get(tt_url)
soup = BeautifulSoup(r.content, 'html.parser')
track_names = []
mp3_urls = []
artwork = []
artist = soup.find("h1", {"class": "profile-bio__name"}).text
dir_path = f"{output_dir}/pyscrapeTrain/{artist}"

# find all tracks on the page to get title and mp3-url
for d in soup.find_all(
        "div",
        {"class": ["js-profile-track", "js-profile-track hidden"]}
):
    # srcset get 2x value, example srcset:
    # srcset="https://d369yr65ludl8k.cloudfront.net/60x60/138296/5d3828d2-7c7e-4d7f-b515-4dd97c83edc9.jpg 1x,
    # https://d369yr65ludl8k.cloudfront.net/120x120/138296/5d3828d2-7c7e-4d7f-b515-4dd97c83edc9.jpg 2x"
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

# url_stub = ""
url_stubs = []

# find url stub for mp3s
scripts = soup.find_all("script")
for script in scripts:
    if "AWS" in script.text:
        s = script.text
        # url_stub = re.search("(?P<url>https?://[^\s]+)\'", s).group("url")
        url_stubs.append(re.search("(?P<url>https?://[^\s]+)\'", s).group("url"))

# make dir if not exists
if not os.path.exists(dir_path):
    os.makedirs(dir_path)


def test_urls(urls, track_name):
    for url in urls:
        try:
            req = Request(url)
            req.add_header('Origin', 'https://traktrain.com')
            req.add_header("Referer", "https://traktrain.com/")
            return urlopen(req).read()
        except HTTPError as e:
            print(f'• Track {track_name} with error {e}, continuing...')
            continue


# use stub and mp3_urls to find all mp3 files on AWS and download them
# avoid stop stealing beats page by adding in origin and referer to request headers
print(f"Downloading {len(mp3_urls)} tracks by {artist}:")
for i in tqdm(range(len(mp3_urls))):
    path = f"{dir_path}/{track_names[i]}.mp3"
    if os.path.exists(path):
        print(f"• {path} already exists, skipping...")
        continue
    urls = [url_stub + mp3_urls[i] for url_stub in url_stubs]
    content = test_urls(urls, track_names[i])
    if content:
        mp3 = MP3(BytesIO(content))
        if mp3.tags is None:
            mp3.tags = ID3()
        # ID3 Frames:
        # https://mutagen.readthedocs.io/en/latest/api/id3_frames.html#id3v2-3-4-frames
        mp3.tags['TPE1'] = TPE1(encoding=3, text=artist)
        mp3.tags['TIT2'] = TIT2(encoding=3, text=track_names[i])
        album_art = urlopen(artwork[i]).read()
        mp3.tags['APIC'] = APIC(
            encoding=3,
            mime='image/jpeg',
            type=3,
            desc=u'Cover',
            data=album_art
        )
        if ALBUM:
            mp3.tags['TALB'] = TALB(encoding=3, text=ALBUM)
        # Save mp3 then save metadata
        with open(path, 'wb') as f:
            f.write(content)
        mp3.save(path)
    else:
        continue
