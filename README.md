# pyscrapeTrain

Python script for downloading all tracks from a traktrain.com url. 
It functions as a TrakTrain downloader to mp3.

Similar functionality to defunct scrapeTrainV2 but written in Python. (I wrote this from scratch as I don't have any experience with Ruby).

# Setup
You can either clone this repo and run the application using the `main.py` file.

If you chose to use this method then run:
```bash
pip install -r requirements.txt
```
And make sure to swap out all the commands in this document with `python main.py` instead of `pyscrapetrain.

OR

Install the pip package, using this command:
```bash
pip install pyscrapetrain
```

# How to use:
## Terminal interface
Feel free to use the built in terminal interface to download tracks from a single URL / artist name:
```bash
pyscrapetrain
```
![image](https://raw.githubusercontent.com/tim-morriss/pyscrapeTrain/dev/terminal_ui.png)


## CLI interface
```bash
pyscrapetrain <traktrain url or artist name>
```

For example: 
```bash
pyscrapetrain https://traktrain.com/brknglss
```
OR
```bash
pyscrapetrain brknglss
```

Tracks are downloaded to a `pyscrapeTrain/artist` folder in your home directory. 
## Changing folder
To change download folder use the `-d` flag:
```bash
pyscrapetrain <traktrain-url> -d /path/to/folder
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
