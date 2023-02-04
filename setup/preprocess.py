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

for tikr in tikrs:
    print(f"{tikr} :Downloading")
    # download raw data from SEC EDGAR
    loader.query_server(tikr, force=args.force, filing_type=FilingType.FILING_10Q)
    time.sleep(5)
    # Unpack downloaded files into relevant directories
    loader.unpack_bulk(tikr, loading_bar=True, force = args.force, desc=f"{tikr} :Inflating HTM")
    metadata.load_tikr_metadata(tikr)
    annotated_docs = parser.get_annotated_submissions(tikr)

    if(args.demo):
        annotated_docs = [annotated_docs[0]]

    for doc in annotated_docs:
        fname = metadata.get_10q_name(tikr, doc)
        parser.featurize_file(tikr, doc, fname,force = args.force) 


s = EDGAR.subset(tikrs=tikrs, debug=True)

#### Load the saved tokenizer
raw_data = s.save_raw_data( fname = "raw_data.npy")
tokenizer = s.build_tokenizer(save = True)
