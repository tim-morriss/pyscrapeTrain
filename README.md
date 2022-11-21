# pyscrapeTrain

Python script for downloading all tracks from a traktrain.com url. It functions as a TrakTrain downloader to mp3.

Similar functionality to defunct scrapeTrainV2 but written in Python. (I wrote this from scratch as I don't have any experience with Ruby).

## Setup
First install the requirements file at the root of the project:
```bash
pip install -r requirements.txt
```

## How to use:
Simplest use-case:
```bash
python scrapeTrain.py <traktrain-url>
```

For example: 
```bash
python scrapeTrain.py https://traktrain.com/waifu
```

Tracks are downloaded to a `pyscrapeTrain/artist` folder in your home directory. 

To change download folder use the `-d` flag:
```bash
python scrapeTrain.py <traktrain-url> -d /path/to/folder
```

Which will create a `pyscrapeTrain/artist` folder under the path specified.
For example:
```bash
python scrapeTrain.py https://traktrain.com/waifu -d /Users/user/Documents
```
Will create the following folder `/Users/user/Documents/pyscrapeTrain/waifu`.
