# pyscrapeTrain

Python script for downloading all tracks from a traktrain.com url. 
It functions as a TrakTrain downloader to mp3.

Similar functionality to defunct scrapeTrainV2 but written in Python. (I wrote this from scratch as I don't have any experience with Ruby).

# Setup
First install the pip package
```bash
pip install pyscrapetrain
```

# How to use:
Simplest use-case:
```bash
pyscrapetrain <traktrain-url>
```

For example: 
```bash
pyscrapetrain https://traktrain.com/waifu
```

Tracks are downloaded to a `pyscrapeTrain/artist` folder in your home directory. 
## Changing folder
To change download folder use the `-d` flag:
```bash
python pyscrapetrain.py <traktrain-url> -d /path/to/folder
```

Which will create a `pyscrapeTrain/artist` folder under the path specified.
For example:
```bash
pyscrapetrain https://traktrain.com/waifu -d /Users/user/Documents
```
Will create the following folder `/Users/user/Documents/pyscrapeTrain/waifu`.

## Adding custom album
You might want to listen to the playlist of tracks you just downloaded 
so the script supports a custom album ID3 tag to allow you to sort in your media library.

Use the `-a` tag to assign a custom album name.

For example:
```bash
pyscrapetrain https://traktrain.com/waifu -a "tt waifu"
```

Which gives:
![image](https://raw.githubusercontent.com/tim-morriss/pyscrapeTrain/master/album%20example.png)

## Supplying a list of URLs

If you want to scrape multiple traktrain pages then you can point a .txt file 
with each url you want to scrape on a new line.

For this use-case simply specify the filepath instead of a url.

For example:
```bash
pyscrapetrain example_url_list.txt
```

Example list of urls:
![image](https://raw.githubusercontent.com/tim-morriss/pyscrapeTrain/master/example%20url%20list.png)
