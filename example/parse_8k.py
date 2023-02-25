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
    tikrs = ['aapl']

for tikr in tqdm(tikrs, desc='Processing...',  position=0):
    # if no submissions, download data from edagr database
    if len(parser.metadata._get_tikr(tikr)['submissions']) == 0:
        EDGAR.load_files(
            tikr, document_type='8k', force_remove_raw=remove,
            silent=silent, data_dir=DATA_DIR)
    # find all the submission based on tikr

 
    submissions = loader.get_submissions(tikr,document_type=document_type)
    
    if args.demo:
        submissions = [submissions[0]]

    # each submission is a raw file
    for submission in tqdm(submissions, 'reading submission...', position=1):
        # parse each raw file to get the text attr
        text = parser.parse_all_text(
            tikr=tikr,
            submission=submission,
            document_type=document_type
            )
        date = loader.metadata._get_submission(tikr, submission)['attrs'].get(
                'FILED AS OF DATE', None)
        print(date)

