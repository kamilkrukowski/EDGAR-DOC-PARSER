"""
    This file will downloads and parses financial data from the SEC EDGAR database for a list of companies specified in the "tickers.txt" file. 
    TThe data is then processed and saved as a tokenizer and raw data file in the current directory.
"""

import os
import time

import sys; 
sys.path.append('..')


from tqdm.auto import tqdm
from secedgar import FilingType
import argparse
import EDGAR



# Command line magic for common use case to regenerate dataset
#   --force to overwrite outdated local files
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--force', action='store_true')
parser.add_argument('-nflx', '--demo', action='store_true')
args = parser.parse_args()

data_dir = "data"
loader = EDGAR.downloader(data_dir=data_dir);
metadata = EDGAR.metadata(data_dir=data_dir)
parser = EDGAR.parser(data_dir=data_dir)



# List of companies to process
tikrs = open(os.path.join(loader.path, 'tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]
if args.demo:
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
        loader.query_server(tikr, force=args.force, filing_type=FilingType.FILING_10Q)
        time.sleep(5)

for tikr in tikrs:
    # Unpack downloaded files into relevant directories
    loader.unpack_bulk(tikr, loading_bar=True, force = args.force, desc=f"{tikr} :Inflating HTM")
    annotated_docs = parser.get_annotated_submissions(tikr)

    if(args.demo):
        annotated_docs = [annotated_docs[0]]

    # to process the documents and extract relevant information. 
    for doc in annotated_docs:
        fname = metadata.get_10q_name(tikr, doc)
        parser.featurize_file(tikr, doc, fname,force = args.force) 


s = EDGAR.subset(tikrs=tikrs, debug=True)

#### saves the raw data
#raw_data = s.save_raw_data( fname = "..\\data\\raw_data.npy")

#### generate and save tokenizer
tokenizer = s.build_tokenizer(save = True,)
