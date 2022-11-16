"""
    This file will featurize the 10-ticker companies and saved the cached feature pandas dataframe
    That dataframe can be loaded for downstream transformations, such as selection of subfields which is done below and saved in a sample_data.csv
"""
import os
import sys ; sys.path.append('..')


from tqdm.auto import tqdm
import numpy as np


import EDGAR

data_dir = os.path.join('..', 'data')

metadata = EDGAR.metadata(data_dir=data_dir)
loader = EDGAR.downloader(data_dir=data_dir);
parser = EDGAR.parser(data_dir=data_dir)

# List of companies to process
tikrs = open(os.path.join(loader.path, '..', 'tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]

trainset = []
for tikr in tikrs:
    metadata.load_tikr_metadata(tikr)
    annotated_docs = parser.get_annotated_submissions(tikr)
 
    for doc in tqdm(annotated_docs, desc=f"Processing {tikr}", leave=False):
        fname = metadata.get_10q_name(tikr, doc)

        # Try load cached, otherwise regenerate new file
        features = parser.featurize_file(tikr, doc, fname) 
    
        found_indices = np.unique([int(i) for i in features['found_index']])
        # Structure: Text str, Labels dict, labelled bool
        data = {i:{'text':None, 'labels':dict(), 'labelled':False } for i in found_indices}
        
        for i in range(len(features)):
            i = features.iloc[i, :]
            # Skip documents which are NOT annotated
            if not i['is_annotation']:
                continue;
            d = data[i['found_index']]
            if d['text'] is None:
                d['text'] = i['text']
            d['labels'][i['annotation_index']] = i['name']
        
        # Add all labelled documents to trainset
        for i in data:
            #Only add labelled documents to trainset
            if not data[i]['is_annotation']:
                continue; 
            d = data[i]
            # Data format: (x,y) where x refers to training features (present for unnannotated docs), and y refers to labels to predict
            # TODO: Convert to list of [lists of tuples, page number, parent_company_tikr] scheme where each list of tuples consists of all annotated webelements on that page
            trainset.append((d['text'], list(d['labels'].values())))
            
    
        # Sample CSV with text, tag information
        with open(os.path.join('..','outputs','sample_data.csv'), 'w') as f:
            text, labels = trainset[0]
            f.write(f"{text},{':'.join([str(i) for i in labels])}")
            for text, labels in trainset[1:]:
                f.write(f"\n{text},{';'.join([str(i) for i in labels])}")

    