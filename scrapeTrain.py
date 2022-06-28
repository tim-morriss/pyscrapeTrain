import requests
import re
import os
import argparse
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from urllib.error import HTTPError

home_path = str(Path.home())

parser = argparse.ArgumentParser(description="Script for downloading traktrain tracks.")
parser.add_argument('url', type=str, help="url for the traktrain profile")

args = parser.parse_args()
tt_url = args.url
artist = tt_url.rsplit('/', 1)[-1]

r = requests.get(tt_url)
soup = BeautifulSoup(r.content, 'html.parser')
track_names = []
mp3_urls = []

for d in soup.find_all("div", {"class": "js-profile-track"}):
    track_names.append(d.find("div", {"class": "title__name-tooltip"}).text.strip('\n'))
    mp3_urls.append(d.find(attrs={"data-id": True})['data-id'])
    # print(url['data-id'])

# print(track_names)
# print(mp3_urls)

url_stub = ""

scripts = soup.find_all("script", {"type": "text/javascript"})
for script in scripts:
    # print(stub)
    if "var AWS_BASE_URL" in script.text:
        s = script.text
        url_stub = re.search("(?P<url>https?://[^\s]+)\'", s).group("url")

dir_path = f"{home_path}/pyscrapeTrain/{artist}"

if not os.path.exists(dir_path):
    os.makedirs(dir_path)

print(f"Downloading {len(mp3_urls)} tracks by {artist}:")
for i in tqdm(range(len(mp3_urls))):
    url = url_stub + mp3_urls[i]
    req = Request(url)
    req.add_header('Origin', 'https://traktrain.com')
    req.add_header("Referer", "https://traktrain.com/")
    try:
        content = urlopen(req).read()
        with open(f"{dir_path}/{track_names[i]}.mp3", 'wb') as f:
            f.write(content)
    except HTTPError as e:
        print(f"{e} \nfor track '{track_names[i]}' with url: {url}, continuing....")
        continue
