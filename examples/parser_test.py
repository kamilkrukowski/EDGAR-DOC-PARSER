# # Issue Found
# - in `labels in tables`, the numpy zeros_like does not handle empty array properly

# Before running, change the file name `parser-mix.py` to `parser`


import os
from time import time
import argparse
import warnings
import sys ; sys.path.append('..')


from tqdm.auto import tqdm
import numpy as np


import EDGAR

data_dir = 'data';
parser = EDGAR.parser(data_dir=data_dir)
metadata = EDGAR.metadata(data_dir=data_dir)
tikr = 'nflx';
parser.metadata.load_tikr_metadata(tikr)
annotated_docs = parser.get_annotated_submissions(tikr, silent=False)
metadata.data_dir



# to process the documents and extract relevant information. 
start = time()
for doc in tqdm(annotated_docs, desc="Parsing...", leave=False):
    fname = metadata.get_10q_name(tikr, doc)
    elems_n, annot_n, in_table_n = parser.new_parse_annotated_text(parser.new_get_driver_path(tikr, doc, fname))
    print('a', end = '')
    elems_o, annot_o, in_table_o = parser._parse_annotated_text(parser.get_driver_path(tikr, doc, fname))
    print('b', end = '')
    
    elems2 = parser.new_parse_unannotated_text(parser.new_get_driver_path(tikr, doc, fname))
    print('c')
    break
elapsed = time()-start
print(f"Elapsed Time for {len(annotated_docs)} documents is {elapsed:.2f} seconds")

def compare_found(a, b):
    a_text = [i.text.strip() for i in a]
    b_text = [i.text.strip() for i in b]
    print('a:')
    for a_t in a_text:
        if a_t not in b_text:
            print(a_t)
    print('\n\n\n\n\n b:')
    for b_t in b_text:
        if b_t not in a_text:
            print(b_t)
    return True

compare_found(elems_o, elems_n)

