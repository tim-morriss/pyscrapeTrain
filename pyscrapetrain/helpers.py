import os
import re
import unicodedata
from urllib.parse import urlparse
from urllib.error import HTTPError
from urllib.request import Request, urlopen


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
