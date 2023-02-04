import os
import time

import sys; 
sys.path.append('..')



from secedgar import FilingType


import EDGAR


data_dir = "data"
loader = EDGAR.downloader(data_dir=data_dir);
metadata = EDGAR.metadata(data_dir=data_dir)
parser = EDGAR.parser(data_dir=data_dir)



# List of companies to process
tikrs = open(os.path.join(loader.path, 'tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]

for tikr in tikrs:
    loader.metadata.load_tikr_metadata(tikr)

# download raw data from SEC EDGAR
to_download = [];
print(f"Forcing Downloads...")
for tikr in tikrs:
    to_download.append(tikr)

# Unpack downloaded files into relevant directories
to_unpack = []
for tikr in tikrs:
    if not loader._is_10q_unpacked(tikr) or args.force:
        to_unpack.append(tikr)

if len(to_unpack) != 0:
    for tikr in to_unpack:
        loader.unpack_bulk(tikr, loading_bar=True, desc=f"{tikr} :Inflating HTM")

# generate raw data from unpack data
parser.featurize_file(tikr, doc, fname,force = True) 
s = EDGAR.subset(tikrs=tikrs, debug=True)

#### Load the saved tokenizer
tokenizer = s.build_tokenizer()