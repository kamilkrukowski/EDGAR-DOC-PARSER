import os
import time
import sys ; sys.path.append('../')
from time import time


from tqdm.auto import tqdm
import numpy as np


import EDGAR


data_dir = os.path.join('..', 'data')
api_keys_path = os.path.join('..','api_keys.yaml')

metadata = EDGAR.Metadata(data_dir=data_dir)
loader = EDGAR.dataloader(data_dir=data_dir, api_keys_path=api_keys_path,metadata=metadata);
parser = EDGAR.parser(data_dir=data_dir, metadata=metadata)

# List of companies to process
tikrs = open(os.path.join(loader.path, '..', 'tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]
tikrs = ['nflx']

trainset = []
for tikr in tikrs:
    metadata.load_tikr_metadata(tikr)
    annotated_docs = parser.get_annotated_submissions(tikr)
 
    for doc in tqdm(annotated_docs, desc=f"Processing {tikr}", leave=False):
        fname = metadata.get_10q_name(tikr, doc)

        features = parser.process_file(tikr, doc, fname) 

        found_indices = np.unique([int(i) for i in features['found_index']])
        data = {i:{'text':None, 'labels':dict(), 'labelled':False } for i in found_indices}
        
        for i in range(len(features)):
            i = features.iloc[i, :]
            if not i['is_annotation']:
                continue;
            d = data[i['found_index']]
            d['labelled'] = True
            if d['text'] is None:
                d['text'] = i['value']
            d['labels'][i['annotation_index']] = i['name']
        
        for i in data:
            d = data[i]
            if not d['labelled']:
                continue; 
            trainset.append((d['text'], list(d['labels'].values())))
    
        with open(os.path.join('..','outputs','sample_data.csv'), 'w') as f:
            text, labels = trainset[0]
            f.write(f"{text},{':'.join([str(i) for i in labels])}")
            for text, labels in trainset[1:]:
                f.write(f"\n{text},{';'.join([str(i) for i in labels])}")

    