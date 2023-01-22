import os
import time

import sys; sys.path.append('..')
import argparse


from secedgar import FilingType


import EDGAR

# Command line magic for common use case to regenerate dataset
#   --force to overwrite outdated local files
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--force', action='store_true')
args = parser.parse_args()

loader = EDGAR.downloader(data_dir=os.path.join('..','data'));

# List of companies to process
tikrs = open(os.path.join(loader.path, os.path.join('..','tickers.txt'))).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]

for tikr in tikrs:
    loader.metadata.load_tikr_metadata(tikr)

to_download = [];
if args.force:
    print(f"Forcing Downloads...")
    for tikr in tikrs:
        to_download.append(tikr)
else:
    # Download missing files
    for tikr in tikrs:
        if not loader._is_downloaded(tikr):
            to_download.append(tikr)
    print(f"Downloaded: {str(list(set(tikrs) - set(to_download)))}")

if len(to_download) == 0:
    print('Everything on Ticker List already downloaded.')
else:
    print(f"Downloading... {str(to_download)}")
    for tikr in to_download:
        loader.query_server(tikr, force=args.force, filing_type=FilingType.FILING_10Q)
        time.sleep(5)


# Unpack downloaded files into relevant directories
to_unpack = []
for tikr in tikrs:
    if not loader._is_10q_unpacked(tikr) or args.force:
        to_unpack.append(tikr)

if len(to_unpack) != 0:
    if args.force:
        print(f"Forcing Unpacking...")
    else:
        print(f"Unpacked: {str(list(set(tikrs) - set(to_unpack)))}")
    print(f"Unpacking... {str(to_unpack)}")
    for tikr in to_unpack:
        loader.unpack_bulk(tikr, loading_bar=True, desc=f"{tikr} :Inflating HTM")
else:
    print('All downloaded 10-Q files already unpacked')
