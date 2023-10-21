import re
import os
import sys
import argparse
import requests
import validators
from halo import Halo
from io import BytesIO
from icecream import ic
from pathlib import Path
from mutagen.mp3 import MP3
from bs4 import BeautifulSoup
from simple_chalk import chalk
from urllib.error import HTTPError
from urllib.request import urlopen
import pyscrapetrain.helpers as helpers
from simple_term_menu import TerminalMenu
from mutagen.id3 import ID3, TPE1, TIT2, TALB, APIC


class PyScrapeTrain:
    def __init__(
            self,
            url: str,
            output_dir: str
    ):
        self.url = url
        self.soup = self._get_soup(url)
        self.artist_name = self._get_artist_name(self.soup)
        self.dir_path = f"{output_dir}/{self.artist_name}"
        self.artwork = []
        self.track_names = []
        self.mp3_urls = []
        self.url_stubs = []

    @staticmethod
    def _get_soup(url: str):
        """
        Returns soup object of page if valid TrakTrain url.

        :param url: str
            TrakTrain URL for artist page.
        :return: BeautifulSoup
            Soup object of page
        """
        if not validators.url(url):
            url = "https://traktrain.com/" + url
        # ic(url)
        if not helpers.is_tt_url(url):
            print(chalk.red.bold("✖ Doesn't look like a TrakTrain.com url..."))
            exit()
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')
        if soup.find("div", {"class": "title-404"}):
            print(chalk.red.bold(f"✖ The url {url} returns 404..."))
            exit()
        return soup

    @staticmethod
    def _get_artist_name(soup: BeautifulSoup):
        """
        Returns artist name from TrakTrain artist page soup object.

        :param soup: BeautifulSoup
            soup object of artist page on traktrain
        :return: str
            artist name
        """
        return helpers.slugify(
            soup.find(
                "h1",
                {"class": "profile-bio__name"}
            ).text
        ).strip()

    def _get_data_endpoint(self):
        """
        Function to find data endpoint from tt page.
        Data endpoint is where tt pulls the track information for artists.

        :return: str
            string of the data-endpoint
        """
        data_endpoint = self.soup.find(
            "form",
            {"class": 'js-filter-form'}
        )
        if data_endpoint.attrs.get('data-endpoint', False):
            return data_endpoint.attrs['data-endpoint'].split('/')[-1]
        else:
            print(
                chalk.red.bold(
                    f"✖ {self.artist_name} doesn't seem to have any tracks..."
                )
            )
            exit()

    def _compile_tracklist(self, data_endpoint: str):
        stop = True
        i = 0

        while stop:
            i += 1
            url = (f"https://traktrain.com/profile-tracks/"
                   f"{data_endpoint}?search=&sort=latest&page={i}")
            r = requests.get(url)
            soup = BeautifulSoup(r.json()['content'], 'html.parser')
            if soup.find("div", {"class": "empty-search"}):
                stop = False
            else:
                for d in soup.find_all(
                        "div",
                        {
                            "class": [
                                "js-profile-track",
                                "js-profile-track hidden"
                            ]
                        }
                ):
                    self.artwork.append(
                        d.find(
                            "img",
                            attrs={"src": True}

                        )['src'].replace('60x60', '360x360')
                    )
                    track_name = helpers.slugify(d.find(
                            "div",
                            {"class": "title__name-tooltip"}
                        ).text.strip('\n'), allow_unicode=True)
                    if track_name in self.track_names:
                        self.track_names.append(track_name + "_1")
                    else:
                        self.track_names.append(track_name)
                    self.mp3_urls.append(
                        d.find(attrs={"data-id": True})['data-id'])

    def _get_tracks(self):
        """
        Returns TrakTrain object of given traktrain profile.

        :return:
            Returns a TrakTrain Object
        """
        data_endpoint = self._get_data_endpoint()
        self._compile_tracklist(data_endpoint)

    def _get_content_urls(self):
        scripts = self.soup.find_all("script")
        for script in scripts:
            if "AWS" in script.text:
                s = script.text
                self.url_stubs.append(
                    re.search(
                        "(?P<url>https?://[^\s]+)\'",
                        s
                    ).group("url"))

    def download_tracks(
            self,
            overwrite: bool,
            album: str = None
    ):
        # get a list of tracks with names, artwork urls and mp3 urls
        self._get_tracks()

        # get a list of content endpoint (traktrain uses AWS to store mp3s)
        self._get_content_urls()

        # make dir if not exists
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)

        # use stub and mp3_urls to find all mp3 files on AWS and download them
        # avoid stop stealing beats page by adding in origin and referer to
        # request headers
        length_of_mp3_urls = len(self.mp3_urls)
        print(chalk.white.bold("-" * 10))
        print(chalk.white.bold(
            f'Downloading {length_of_mp3_urls} tracks by {self.artist_name}:'
        ))

        for i in range(len(self.mp3_urls)):
            num = i + 1
            with Halo(
                    text=chalk.magenta(
                        f'Downloading track {num} of {length_of_mp3_urls}: '
                        f'{self.track_names[i]}...'
                    ),
                    spinner="dots"
            ) as halo:
                path = f"{self.dir_path}/{self.track_names[i]}.mp3"
                if os.path.exists(path) and not overwrite:
                    halo.stop_and_persist(
                        symbol=str(f'{chalk.yellow("〰")}'),
                        text=chalk.yellow.dim(
                            f"{num} • {path} already exists, skipping..."
                        )
                    )
                    continue
                urls = [
                    url_stub + self.mp3_urls[i] for url_stub in self.url_stubs
                ]
                content = helpers.test_urls(urls)
                if content:
                    mp3 = MP3(BytesIO(content))
                    if mp3.tags is None:
                        mp3.tags = ID3()
                    # ID3 Frames:
                    # https://mutagen.readthedocs.io/en/latest/api
                    # /id3_frames.html
                    # #id3v2-3-4-frames
                    mp3.tags['TPE1'] = TPE1(
                        encoding=3, text=self.artist_name
                    )
                    mp3.tags['TIT2'] = TIT2(
                        encoding=3, text=self.track_names[i]
                    )
                    try:
                        album_art = urlopen(self.artwork[i]).read()
                    except HTTPError:
                        album_art = helpers.try_artwork(self.artwork[i])
                    mp3.tags['APIC'] = APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,
                        desc=u'Cover',
                        data=album_art
                    )
                    if album:
                        mp3.tags['TALB'] = TALB(encoding=3, text=album)
                    # Save mp3 then save metadata
                    with open(path, 'wb') as f:
                        f.write(content)
                    mp3.save(path)
                    halo.stop_and_persist(
                        symbol=f'{chalk.green("✔")}',
                        text=chalk.green.dim(
                            f"{num} Saved "
                            f"{chalk.white.bold(self.track_names[i])} "
                            f"{chalk.green.dim(path)}"
                        )
                    )
                else:
                    halo.stop_and_persist(
                        symbol=str(f'{chalk.red("✖")}'),
                        text=chalk.red.dim(
                            f'{num} Traktrain error skipping '
                            f'{self.track_names[i]}'
                        )
                    )
                    continue


def term_menu(options, title):
    terminal_menu = TerminalMenu(options, title=title)
    menu_entry_index = terminal_menu.show()
    return menu_entry_index


def cli():
    parser = argparse.ArgumentParser(
        description="Tool for downloading TrakTrain tracks."
    )

    parser.add_argument(
        'url',
        nargs='?',
        default=None,
        type=str,
        help="url for the traktrain profile",
    ),
    parser.add_argument(
        '-d',
        '--dir',
        dest='directory',
        default=None,
        type=str,
        help="directory to save mp3s to. format: <dir>/pyscrapetrain/<artist>"
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

    if sys.argv[1:]:
        args = parser.parse_args(args=sys.argv[1:])
        if not args.directory:
            # os agnostic home path
            output_dir = str(Path.home()) + '/pyscrapetrain'
        else:
            output_dir = args.directory
        # define where to save mp3s
        album = args.album
        overwrite = args.overwrite
        url = args.url
        return output_dir, album, overwrite, url
    else:
        first_menu_options = [
            "[s] Download an artist's tracks",
            "[e] Exit program"
        ]
        first_menu_index = term_menu(first_menu_options, "pyscrapeTrain")
        if first_menu_index == 0:
            url = input("Enter the URL of the artist you want to scrape: ")
            output_dir = input("What is the output directory you want to use "
                               "(leave blank for default): ") or str(Path.home()) + '/pyscrapetrain'
            overwrite_menu_options = [
                "[y] Yes",
                "[n] No"
            ]
            overwrite_menu_index = term_menu(
                overwrite_menu_options,
                "Overwrite files if they already exist?"
            )
            if overwrite_menu_index == 0:
                overwrite = True
            else:
                overwrite = False
            album = input("Do you want to save the output with an album ID3 "
                          "tag (good for sorting in your music library, "
                          "leave blank to turn off): ") or None
            return output_dir, album, overwrite, url
        if first_menu_index == 1:
            exit()


def run():

    output_dir, album, overwrite, url = cli()

    if helpers.is_local(url):
        try:
            if url.endswith('.txt'):
                with open(url) as f:
                    lines = f.readlines()
                    lines = list(set(lines))
                    for line in lines:
                        try:
                            PyScrapeTrain(
                                line.strip(),
                                output_dir
                            ).download_tracks(
                                overwrite,
                                album
                            )
                        except Exception as e:
                            print(e)
            else:
                raise Exception("Please supply a txt file")
        except Exception as e:
            print(e)
    else:
        PyScrapeTrain(url, output_dir).download_tracks(overwrite, album)
