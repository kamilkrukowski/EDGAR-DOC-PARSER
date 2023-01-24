import os
import sys ; sys.path.append('..')


from tqdm.auto import tqdm
import numpy as np
import argparse
import warnings


import EDGAR

data_dir = 'data'
metadata = EDGAR.metadata(data_dir=data_dir)
loader = EDGAR.downloader(data_dir=data_dir);
parser = EDGAR.parser(data_dir=data_dir)

# List of companies to process
tikrs = open(os.path.join(metadata.path, 'tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]
# tikrs = ['nflx']

d = EDGAR.dataloader(tikrs=tikrs, debug=True)

max_vocab = list(d.vocab.keys())
max_labels = list(d.labels.keys())