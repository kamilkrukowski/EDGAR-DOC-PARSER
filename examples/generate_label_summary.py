import os
import time
import sys ; sys.path.append('../')
from time import time


import EDGAR


data_dir = os.path.join('..', 'data')
api_keys_path = os.path.join('..','api_keys.yaml')

metadata = EDGAR.Metadata(data_dir=data_dir)
loader = EDGAR.dataloader(data_dir=data_dir, api_keys_path=api_keys_path,metadata=metadata);
parser = EDGAR.parser(data_dir=data_dir, metadata=metadata)

# List of companies to process
tikrs = open(os.path.join(loader.path, '..', 'tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]

trainset = []
for tikr in tikrs:
    metadata.load_tikr_metadata(tikr)
    annotated_docs = parser.get_annotated_submissions(tikr)
    
    for doc in annotated_docs:
        fname = metadata.get_10q_name(tikr, doc)
        elems, annotation_dict = parser._parse_annotated_text(parser.get_driver_path(tikr, doc, fname))

        # TODO collect summary statistics on parsed information 

        break
    break;




