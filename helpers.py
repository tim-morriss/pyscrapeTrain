import os
import re
import requests
import unicodedata
from typing import List
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class TrakTrain:
    def __init__(
            self,
            artist: str,
            artwork: List[str],
            track_names: List[str],
            mp3_urls: List[str],
            soup: BeautifulSoup,
            dir_path: str
    ):
        self.artist = artist
        self.artwork = artwork
        self.track_names = track_names
        self.mp3_urls = mp3_urls
        self.soup = soup
        self.dir_path = dir_path


def is_local(url: str):
    """
    Parse url and check if it is a local file or a web url

    :param url:
        str: url to parse
    :return: bool
    """
    url_parsed = urlparse(url)
    if url_parsed.scheme in ('file', ''):  # Possibly a local file
        return os.path.exists(url_parsed.path)
    return False


def slugify(value: str, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils
    /text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii',
                                                            'ignore').decode(
            'ascii')
    # value = re.sub(r'[^\w\s-]', '', value.lower())
    value = re.sub(r'[^\w\s-]', '', value)
    return re.sub(r'[-\s]+', ' ', value).strip('-_')


def test_urls(urls: list):
    """
    Test TrakTrain url to see if it raises HTTPError or not.
    Note: some tracks are not available from the AWS server,
    this is an issue with Traktrain.

    :param urls:
        list: list of urls to test
    :return:
        urlopen object
    """
    for url in reversed(urls):
        try:
            req = Request(url)
            req.add_header('Origin', 'https://traktrain.com')
            req.add_header("Referer", "https://traktrain.com/")
            return urlopen(req).read()
        except HTTPError:
            continue


def try_artwork(artwork: str):
    """
    Try artwork sizes to see if they can be accessed successfully.

    :param artwork:
        list: Artwork to test
    :return:
        urlopen object
    """
    sizes = [
        # '360x360',
        '250x250',
        '120x120',
        '60x60'
    ]
    for size in sizes:
        try:
            return urlopen(artwork.replace('360x360', size)).read()
        except HTTPError:
            continue


def is_tt_url(tt_url: str):
    """
    Check to see if url starts with traktrain.com

    :param tt_url:
        string: url to test
    :return:
        bool: True if it is a traktrain url, else False
    """
    if tt_url.startswith("https://traktrain.com/"):
        return True
    elif tt_url.startswith("https://www.traktrain.com/"):
        return True
    else:
        return False


def get_data_endpoint(soup: BeautifulSoup, artist: str):
    """
    Function to find data endpoint from tt page.
    Data endpoint is where tt pulls the track information for artists.

    :param soup:
        tt beautifulsoup object
    :return:
        string of the data-endpoint
    """
    data_endpoint = soup.find(
        "form",
        {"class": 'js-filter-form'}
    )
    if data_endpoint.attrs.get('data-endpoint', False):
        return data_endpoint.attrs['data-endpoint'].split('/')[-1]
    else:
        raise Exception(f"{artist} doesn't seem to have any tracks...")


def compile_page(data_endpoint: str):
    stop = True
    i = 0
    track_names = []
    mp3_urls = []
    artwork = []

    while stop:
        i += 1
        url = f"https://traktrain.com/profile-tracks/{data_endpoint}?search=&sort=latest&page={i}"
        r = requests.get(url)
        soup = BeautifulSoup(r.json()['content'], 'html.parser')
        if soup.find("div", {"class": "empty-search"}):
            stop = False
        else:
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

    return track_names, mp3_urls, artwork


def get_tracks(tt_url: str, output_dir: str):
    """
    Returns TrakTrain object of given traktrain profile.

    :param tt_url: str
        URL for TrakTrain profile
    :param output_dir: str
        Output directory for the files
    :return:
        Returns a TrakTrain Object
    """
    if not is_tt_url(tt_url):
        raise Exception("Doesn't look like a TrakTrain.com url...")
    r = requests.get(tt_url)
    soup = BeautifulSoup(r.content, 'html.parser')

    artist = slugify(
        soup.find("h1", {"class": "profile-bio__name"}).text
    ).strip()
    dir_path = f"{output_dir}/{artist}"

    data_endpoint = get_data_endpoint(soup, artist)
    track_names, mp3_urls, artwork = compile_page(data_endpoint)

    return TrakTrain(artist, artwork, track_names, mp3_urls, soup, dir_path)
