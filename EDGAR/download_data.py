import os
import time


from dataloader import edgar_dataloader


loader = edgar_dataloader('edgar_downloads')

# List of companies to process
tikrs = open(os.path.join(loader.path, '../tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]

# Check if some are already downloaded, do not redownload
to_download = [];
for tikr in tikrs:
    if not loader.__check_downloaded__(tikr):
        to_download.append(tikr)

# Download missing files
print(f"Downloaded: {str(list(set(tikrs) - set(to_download)))}")
if len(to_download) != 0:
    print(f"Downloading... {str(to_download)}")
    for tikr in to_download:
        loader.__query_server__(tikr)
else:
    print('Everything Downloaded.')

# Unpack downloaded files into relevant directories
print("Processing Raw Submissions");
for tikr in tikrs:
    loader.unpack_bulk(tikr, loading_bar=True, desc=f"{tikr} :Inflating HTM")
