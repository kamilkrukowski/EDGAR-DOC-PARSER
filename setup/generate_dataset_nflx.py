"""
    This file will featurize the 10-ticker companies and saved the cached feature pandas dataframe
    That dataframe can be loaded for downstream transformations, such as selection of subfields which is done below and saved in a sample_data.csv
"""
import os
import sys ; sys.path.append('../')


from tqdm.auto import tqdm
import numpy as np


import EDGAR


data_dir = os.path.join('..', 'data')
api_keys_path = os.path.join('..','api_keys.yaml')

metadata = EDGAR.Metadata(data_dir=data_dir)
loader = EDGAR.dataloader(data_dir=data_dir, api_keys_path=api_keys_path,metadata=metadata);
parser = EDGAR.parser(data_dir=data_dir, metadata=metadata)

tikr = "nflx"

metadata.load_tikr_metadata(tikr)
annotated_docs = parser.get_annotated_submissions(tikr)

trainset = []

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
            d['text'] = [i['value'], i["full_text"]]

        d['labels'][i['annotation_index']] = []
        for _attr in ['name', 'id', 'contextref', 'decimals', 'format', 'unitref']:
            d['labels'][i['annotation_index']].append(i[_attr])
    for i in data:
        d = data[i]
        if not d['labelled']:
            continue; 
        trainset.append((d['text'], list(d['labels'].values())))
        

    with open(os.path.join('..','outputs','sample_data_nflx.csv'), 'w') as f:
        text, labels = trainset[0]
        f.write(f"{text},{':'.join([str(i) for i in labels])}")
        for text, labels in trainset[1:]:
            f.write(f"\n{text},{';'.join([str(i) for i in labels])}")

    