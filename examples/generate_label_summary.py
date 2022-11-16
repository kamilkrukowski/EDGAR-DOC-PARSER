import os
import sys ; sys.path.append('..')


from tqdm.auto import tqdm


import EDGAR


data_dir = os.path.join('..', 'data')

metadata = EDGAR.metadata(data_dir=data_dir)
loader = EDGAR.downloader(data_dir=data_dir);
parser = EDGAR.parser(data_dir=data_dir, metadata=metadata)

# List of companies to process
tikrs = open(os.path.join(loader.path, '..', 'tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]

labels = dict()
for tikr in tikrs:
    metadata.load_tikr_metadata(tikr)
    annotated_docs = parser.get_annotated_submissions(tikr)
 
    for doc in tqdm(annotated_docs, desc=f"Processing {tikr}", leave=False):
        fname = metadata.get_10q_name(tikr, doc)

        # Try load cached, otherwise regenerate new file
        features = parser.featurize_file(tikr, doc, fname) 
    
        found_indices = np.unique([int(i) for i in features['found_index']])
        # Structure: Text str, Labels dict, labelled bool
        data = {i:{'text':None, 'labels':dict()} for i in found_indices}
        
        for i in range(len(features)):
            i = features.iloc[i, :]
            
            # Skip documents which are NOT annotated
            if not i['is_annotation']:
                continue;

            d = data[i['found_index']]
            
            if d['text'] is None:
                d['text'] = i['value']
            
            d['labels'][i['annotation_index']] = i['name']
        
        # Add all labelled documents to trainset
        for i in data:
            #Only add labelled documents to trainset
            if not data[i]['is_annotation']:
                continue; 
            d = data[i]
            
            for label in d['labels'].values():
                labels[label][tikr] = labels[label].get(tikr, 0) + 1
                labels[label]['total'] = labels[label].get('total', 0) + 1