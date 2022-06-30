# pyscrapeTrain

Python script for downloading all tracks from a traktrain.com url. It functions as a TrakTrain downloader to mp3.

Similar functionality to defunct scrapeTrainV2 but written in Python. (I wrote this from scratch as I don't have any experience with Ruby).

How to use:  
```bash
python scrapeTrain.py <traktrain-url>
```

For example: 
```bash
python scrapeTrain.py https://traktrain.com/waifu
```

Tracks are downloaded to a `scrapeTrain/artist` folder in your home directory. 

Still a WIP, there's no real error reporting to user and no way to change download directory.
