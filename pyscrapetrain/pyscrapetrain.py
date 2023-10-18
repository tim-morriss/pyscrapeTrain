import re
import os
import pyscrapetrain.helpers as helpers
import argparse
import requests
from halo import Halo
from io import BytesIO
from pathlib import Path
from mutagen.mp3 import MP3
from bs4 import BeautifulSoup
from simple_chalk import chalk
from urllib.error import HTTPError
from urllib.request import urlopen
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
        if not helpers.is_tt_url(url):
            raise Exception("Doesn't look like a TrakTrain.com url...")
        r = requests.get(url)
        return BeautifulSoup(r.content, 'html.parser')

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
            raise Exception(
                f"{self.artist_name} doesn't seem to have any tracks..."
            )

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
                    self.track_names.append(
                        helpers.slugify(d.find(
                            "div",
                            {"class": "title__name-tooltip"}
                        ).text.strip('\n'), allow_unicode=True)
                    )
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
        print(chalk.white.bold("-" * 10))
        print(chalk.white.bold(
            f'Downloading {len(self.mp3_urls)} tracks by {self.artist_name}:'
        ))

        for i in range(len(self.mp3_urls)):
            num = i + 1
            with Halo(
                    text=chalk.magenta(
                        f'Downloading track {num}: {self.track_names[i]}...'
                    ),
                    spinner="dots"
            ) as halo:
                path = f"{self.dir_path}/{self.track_names[i]}.mp3"
                if os.path.exists(path) and not overwrite:
                    halo.stop_and_persist(
                        symbol=str(f'{chalk.red("✖")}'),
                        text=chalk.red.dim(
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


def run():
    parser = argparse.ArgumentParser(
        description="Tool for downloading TrakTrain tracks."
    )

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

    args = parser.parse_args()
    if not args.directory:
        # os agnostic home path
        output_dir = str(Path.home()) + '/pyscrapetrain'
    else:
        output_dir = args.directory
    # define where to save mp3s
    album = args.album
    overwrite = args.overwrite

    if helpers.is_local(args.url):
        try:
            if args.url.endswith('.txt'):
                with open(args.url) as f:
                    lines = f.readlines()
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
        tt_url = args.url
        PyScrapeTrain(tt_url, output_dir).download_tracks(overwrite, album)


if __name__ == '__main__':
    run()
