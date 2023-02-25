"""
    preprocess_all.py
    This file will downloads and parses financial data from the SEC EDGAR database for a list of companies specified in the "tickers.txt" file.
    TThe data is then processed and saved as a tokenizer and raw data file in the current directory.
"""

import sys
import os
sys.path.append(os.path.join('..', 'src', 'EDGAR'))
sys.path.append(os.path.join('..', 'src'))
import EDGAR
import torch
import numpy as np
# from transformers import BertTokenizerFast
from tqdm.auto import tqdm
# import os
import time
import itertools
import argparse





# SETTINGS
DATA_DIR = os.path.join("..", "data")#'data'
N_TIKRS = 15

loader = EDGAR.Downloader(data_dir=DATA_DIR)
parser = EDGAR.Parser(data_dir=DATA_DIR)

tikrs = ['aapl', 'msft', 'amzn', 'tsla', 'googl', 'goog',  'unh', 'jnj', 'xom']

document_type = EDGAR.DocumentType('8k')

force = False
silent = True
remove = False

for tikr in tqdm(tikrs, desc='Processing...'):
    print(tikr)
    if len(parser.metadata._get_tikr(tikr)['submissions']) == 0:
        EDGAR.load_files(
            tikr, document_type='8k', force_remove_raw=remove,
            silent=silent, data_dir=DATA_DIR)

    annotated_subs = parser.get_annotated_submissions(tikr, silent=silent)


    for submission in annotated_subs:
        fname = parser.metadata.get_8k_name(tikr, submission)
        if not parser.metadata.file_was_processed(tikr, submission, fname):
            EDGAR.load_files(
                tikr, document_type='8k', force_remove_raw=remove,
                silent=silent, data_dir=DATA_DIR)

    
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
import pandas as pd


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
    
text_list = []
date_list = []
tikr_list = []
submission_list = []
doc_type_list = []

for tikr in tqdm(tikrs, desc='Processing...',  position=0):
    # if no submissions, download data from edagr database
    if len(parser.metadata._get_tikr(tikr)['submissions']) == 0:
        EDGAR.load_files(
            tikr, document_type='8k', force_remove_raw=remove,
            silent=silent, data_dir=DATA_DIR)
    # find all the submission based on tikr

 
    submissions = loader.get_submissions(tikr,document_type=document_type)
    
    if args.demo:
        submissions = submissions[:10]

    # each submission is a raw file
    for submission in tqdm(submissions, 'reading submission...', position=1):
        # parse each raw file to get the text attr
        text = parser.parse_all_text_8k(
            tikr=tikr,
            submission=submission,
            document_type=document_type
            )
        date = loader.metadata._get_submission(tikr, submission)['attrs'].get(
                'FILED AS OF DATE', None)
        
        text_list += [text]
        date_list += [date]
        tikr_list += [tikr]
        submission_list += [submission]
        doc_type_list += [document_type]

df = pd.DataFrame(data = {
        'tikr': tikr_list,
        'document type': doc_type_list,
        'submission': submission_list,
        'text': text_list,
        'date': date_list
        })
df.to_csv('8k_data.csv')

