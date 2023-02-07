"""
Opens a local 'nflx' 8-K form (or tries)
Extracts 'text' elements from HTM tree
Visualizes elements by red border highlighting in firefox browser
"""
import pandas as pd
import numpy as np
from secedgar import FilingType


import os
import time
import argparse

import pathlib
import sys ; sys.path.append('..')


import EDGAR

# Hyperparameters
tikr = 'nflx'
submission_date = '20220101' #Find nearest AFTER this date
headless = False

# Command line magic for common use case to regenerate dataset
#   --force to overwrite outdated local files
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--force', action='store_true')
args = parser.parse_args()

loader = EDGAR.downloader(data_dir=os.path.join('..','data'));

# List of companies to process
# tikrs = open(os.path.join(loader.path, os.path.join('..','tickers.txt'))).read().strip()
# tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]
tikrs = ['nflx']
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
        loader.query_server(tikr, force=args.force, filing_type=FilingType.FILING_8K)
        time.sleep(5)


# Unpack downloaded files into relevant directories
to_unpack = []
for tikr in tikrs:
    if loader._is_8k_unpacked(tikr) or args.force:
        to_unpack.append(tikr)

if len(to_unpack) != 0:
    if args.force:
        print(f"Forcing Unpacking...")
    else:
        print(f"Unpacked: {str(list(set(tikrs) - set(to_unpack)))}")
    print(f"Unpacking... {str(to_unpack)}")
    for tikr in to_unpack:
        loader.unpack_bulk(tikr, complete=False, loading_bar=True, desc=f"{tikr} :Inflating HTM", document_type='8-K')
else:
    print('All downloaded 8-K files already unpacked')

# Set up
loader = EDGAR.downloader(data_dir=os.path.join('..','data'));
loader.metadata.load_tikr_metadata(tikr)
# Get nearest 10Q form path to above date
dname = loader.get_nearest_date_filename(tikr, submission_date, document_type='8-K')
fname = loader.metadata.get_8k_name(tikr, dname)
# fname = loader.metadata.get_10q_name(tikr, dname)

driver_path = pathlib.Path(os.path.join(loader.proc_dir, tikr, dname, fname)).as_uri()

parser = EDGAR.parser(metadata=loader.metadata, headless=headless)

# Parsing
found, annotation_dict, in_table = parser._parse_annotated_text(driver_path, highlight=True, save=False)
texts = []
for element in found:
    texts.append(element.text)
data = parser.get_annotation_features(found, annotation_dict, in_table, save = True)
input("enter to continue")
print(data)
print("DONE")