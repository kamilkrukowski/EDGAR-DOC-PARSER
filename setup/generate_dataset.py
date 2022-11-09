import os
import time
import sys ; sys.path.append('../')
from time import time


import EDGAR


data_dir = '../data'

metadata = EDGAR.Metadata(data_dir=data_dir)
loader = EDGAR.dataloader(data_dir=data_dir, api_keys_path='../api_keys.yaml',metadata=metadata);
parser = EDGAR.parser(data_dir=data_dir, metadata=metadata)

# List of companies to process
tikrs = open(os.path.join(loader.path, '../tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]

trainset = []
for tikr in tikrs:
    metadata.load_tikr_metadata(tikr)
    
    t = time()
    annotated_docs = parser.get_annotated_submissions(tikr)
    
    for doc in annotated_docs:
        fname = metadata.get_10q_name(tikr, doc)
        elems, annotation_dict = parser._parse_annotated_text(parser.get_driver_path(tikr, doc, fname))

        parser.

       # TODO ADD FUNCTION TO GET TRAINING DATA FROM ELEMS, ANNOTATIONS 

        break
    break;




