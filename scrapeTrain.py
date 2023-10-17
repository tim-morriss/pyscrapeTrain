import os
import re
import argparse
import requests
from halo import Halo
from io import BytesIO
from pathlib import Path
from mutagen.mp3 import MP3
from simple_chalk import chalk
from urllib.error import HTTPError
from urllib.request import urlopen
from mutagen.id3 import ID3, TPE1, TIT2, TALB, APIC
from helpers import slugify, is_local, try_artwork, test_urls, get_tracks


def scrape_train(tt_url, output_dir, overwrite):
    """
    Downloads tracks from TrakTrain.com page to output_dir/<artist> name.

    :param tt_url:
        str: url of TrakTrain.com page
    :param output_dir:
        str: path to output directory
    :param overwrite:
        bool: whether to overwrite tracks if exist
    """
    tt = get_tracks(tt_url, output_dir)

    # print(track_names)
    # print(mp3_urls)
    # print(artwork)

    url_stubs = []

    # find url stub for mp3s
    scripts = tt.soup.find_all("script")
    for script in scripts:
        if "AWS" in script.text:
            # print(script)
            s = script.text
            url_stubs.append(
                re.search("(?P<url>https?://[^\s]+)\'", s).group("url"))

    # make dir if not exists
    if not os.path.exists(tt.dir_path):
        os.makedirs(tt.dir_path)

    # use stub and mp3_urls to find all mp3 files on AWS and download them
    # avoid stop stealing beats page by adding in origin and referer to
    # request headers
    print(f"Downloading {len(tt.mp3_urls)} tracks by {tt.artist}:")
    for i in range(len(tt.mp3_urls)):
        num = i + 1
        with Halo(
            text=f"{chalk.magenta(f'Downloading track {num}: {tt.track_names[i]}...')}",
            spinner="dots"
        ) as halo:
            path = f"{tt.dir_path}/{tt.track_names[i]}.mp3"
            if os.path.exists(path) and not overwrite:
                # print(f"• {path} already exists, skipping...")
                halo.stop_and_persist(
                    symbol=str(f'{chalk.red("✖")}'),
                    text=f'{chalk.red.dim(f"{num} • {path} already exists, skipping...")}'
                )
                continue
            urls = [url_stub + tt.mp3_urls[i] for url_stub in url_stubs]
            content = test_urls(urls)
            if content:
                mp3 = MP3(BytesIO(content))
                if mp3.tags is None:
                    mp3.tags = ID3()
                # ID3 Frames:
                # https://mutagen.readthedocs.io/en/latest/api/id3_frames.html
                # #id3v2-3-4-frames
                mp3.tags['TPE1'] = TPE1(encoding=3, text=tt.artist)
                mp3.tags['TIT2'] = TIT2(encoding=3, text=tt.track_names[i])
                try:
                    album_art = urlopen(tt.artwork[i]).read()
                except HTTPError:
                    album_art = try_artwork(tt.artwork[i])
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
                halo.stop_and_persist(
                    symbol=f'{chalk.green("✔")}',
                    text=chalk.green.dim(f"{num} Saved {chalk.white.bold(tt.track_names[i])} {chalk.green.dim(path)}")
                )
            else:
                halo.stop_and_persist(
                    symbol=str(f'{chalk.red("✖")}'),
                    text=f"{chalk.red.dim(f'{num} Traktrain error skipping {tt.track_names[i]}')}"
                )
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
    parser.add_argument(
        '-o',
        '--overwrite',
        dest='overwrite',
        default=False,
        action="store_true"
    )

    args = parser.parse_args()
    if not args.directory:
        # os agnostic home path
        output_dir = str(Path.home()) + '/pyscrapeTrain'
    else:
        output_dir = args.directory
    # define where to save mp3s
    ALBUM = args.album
    overwrite = args.overwrite

    if is_local(args.url):
        try:
            if args.url.endswith('.txt'):
                with open(args.url) as f:
                    lines = f.readlines()
                    for line in lines:
                        try:
                            scrape_train(line.strip(), output_dir, overwrite)
                        except Exception as e:
                            print(e)
            else:
                raise Exception("Please supply a txt file")
        except Exception as e:
            print(e)
    else:
        tt_url = args.url
        scrape_train(tt_url, output_dir, overwrite)
