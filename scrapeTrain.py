import re
import os
from io import BytesIO
import requests
import argparse
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TPE1, TIT2, TALB, APIC
from urllib.error import HTTPError
from urllib.request import urlopen
from helpers import slugify, is_local, try_artworks, test_urls, is_tt_url


def scrape_train(tt_url, output_dir):
    """
    Downloads tracks from TrakTrain.com page to output_dir/<artist> name.

    :param tt_url:
        str: url of TrakTrain.com page
    :param output_dir:
        str: path to output directory
    """
    # get TrakTrain page as beautiful soup object
    if not is_tt_url(tt_url):
        raise Exception("Doesn't look like a TrakTrain.com url...")
    r = requests.get(tt_url)
    soup = BeautifulSoup(r.content, 'html.parser')
    track_names = []
    mp3_urls = []
    artwork = []
    artist = slugify(
        soup.find("h1", {"class": "profile-bio__name"}).text
    ).strip()
    dir_path = f"{output_dir}/{artist}"

    # find all tracks on the page to get title and mp3-url
    for d in soup.find_all(
            "div",
            {"class": ["js-profile-track", "js-profile-track hidden"]}
    ):
        artwork.append(
            d.find(
                "img",
                attrs={"src": True}
            )['src'].replace('60x60', '360x360')
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

    url_stubs = []

    # find url stub for mp3s
    scripts = soup.find_all("script")
    for script in scripts:
        if "AWS" in script.text:
            # print(script)
            s = script.text
            url_stubs.append(
                re.search("(?P<url>https?://[^\s]+)\'", s).group("url"))

    # make dir if not exists
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # use stub and mp3_urls to find all mp3 files on AWS and download them
    # avoid stop stealing beats page by adding in origin and referer to
    # request headers
    print(f"Downloading {len(mp3_urls)} tracks by {artist}:")
    for i in tqdm(range(len(mp3_urls))):
        path = f"{dir_path}/{track_names[i]}.mp3"
        if os.path.exists(path):
            print(f"• {path} already exists, skipping...")
            continue
        urls = [url_stub + mp3_urls[i] for url_stub in url_stubs]
        content = test_urls(urls)
        if content:
            mp3 = MP3(BytesIO(content))
            if mp3.tags is None:
                mp3.tags = ID3()
            # ID3 Frames:
            # https://mutagen.readthedocs.io/en/latest/api/id3_frames.html
            # #id3v2-3-4-frames
            mp3.tags['TPE1'] = TPE1(encoding=3, text=artist)
            mp3.tags['TIT2'] = TIT2(encoding=3, text=track_names[i])
            try:
                album_art = urlopen(artwork[i]).read()
            except HTTPError:
                album_art = try_artworks(artwork[i])
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
            print(f"Traktrain error skipping {track_names[i]}")
            continue


if __name__ == '__main__':
    # cli argument for TrakTrain URL
    parser = argparse.ArgumentParser(
        description="Script for downloading traktrain tracks.")
    parser.add_argument(
        'url',
        type=str,
        help="url for the traktrain profile",
    ),
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
    if not args.directory:
        # os agnostic home path
        output_dir = str(Path.home()) + '/pyscrapeTrain'
    else:
        output_dir = args.directory
    # define where to save mp3s
    ALBUM = args.album

    if is_local(args.url):
        try:
            if args.url.endswith('.txt'):
                with open(args.url) as f:
                    lines = f.readlines()
                    for line in lines:
                        scrape_train(line.strip(), output_dir)
            else:
                raise Exception("Please supply a txt file")
        except Exception as e:
            print(e)
    else:
        tt_url = args.url
        scrape_train(tt_url, output_dir)
