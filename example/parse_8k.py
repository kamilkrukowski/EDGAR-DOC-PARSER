"""
`data` folder placed under EDFAR-DOC-PARSER

"""

import sys
import os
import argparse
import itertools
import time
from tqdm.auto import tqdm
import numpy as np
import torch
sys.path.append(os.path.join('..', 'src', 'EDGAR'))
sys.path.append(os.path.join('..', 'src'))
import EDGAR


parser = argparse.ArgumentParser()
parser.add_argument('-aapl', '--demo', action='store_true')
args = parser.parse_args()
# SETTINGS
DATA_DIR = os.path.join("..", "data")  # 'data'

loader = EDGAR.Downloader(data_dir=DATA_DIR)
parser = EDGAR.Parser(data_dir=DATA_DIR)

# List of companies to process
# List of companies to process
# tikrs = open(os.path.join( '..','tickers.txt')).read().strip()
# tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]
# tikrs = parser.metadata.get_tikr_list()[:N_TIKRS]

tikrs = ['aapl', 'msft', 'amzn', 'tsla', 'googl', 'goog',  'unh', 'jnj', 'xom']

document_type = EDGAR.DocumentType('8k')

force = False
silent = True
remove = False


if args.demo:
    tikrs = ['goog']

for tikr in tqdm(tikrs, desc='Processing...',  position=0):
    # if no submissions, download data from edagr database
    if len(parser.metadata._get_tikr(tikr)['submissions']) == 0:
        EDGAR.load_files(
            tikr, document_type='8k', force_remove_raw=False,
            silent=silent, data_dir=DATA_DIR)
    submissions = loader.get_submissions(tikr,document_type=document_type)
    print(submissions)
    if args.demo:
        submissions = [submissions[0]]

    for submission in tqdm(submissions, 'reading submission...', position=1):
        text = parser.parse_all_text_8k(
            tikr=tikr,
            submission=submission,
            document_type=document_type
            )
        print(text)

