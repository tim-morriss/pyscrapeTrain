import sys
import argparse
from icecream import ic
from pathlib import Path
from simple_chalk import chalk
from simple_term_menu import TerminalMenu
import pyscrapetrain.url_helpers as helpers
from pyscrapetrain.config import __version__, __title__
from pyscrapetrain.pyscrapetrain import PyScrapeTrain


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
        first_menu_index = term_menu(
            first_menu_options,
            f"{__title__}"
            f"\n Version: {__version__} "
            f"\n Copyright 2022-2023"
        )
        if first_menu_index == 0:
            url = input("Enter the URL or name of the "
                        "artist you want to scrape: ")
            output_dir = (input("What is the output directory you want to use "
                                "(leave blank for default): ")
                          or str(Path.home()) + '/pyscrapetrain')
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
