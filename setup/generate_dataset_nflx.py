"""
    This file will featurize the nflx and saved the cached feature pandas dataframe
    That dataframe can be loaded for downstream transformations, such as selection of subfields which is done below and saved in a sample_data.csv
"""
import os
import sys ; sys.path.append('..')


from tqdm.auto import tqdm
import numpy as np
import argparse
import warnings


import EDGAR


# Command line magic for common use case to regenerate dataset
#   --force to overwrite outdated local files
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--force', action='store_true')
args = parser.parse_args()

data_dir = os.path.join('..', 'data')

metadata = EDGAR.metadata(data_dir=data_dir)
loader = EDGAR.downloader(data_dir=data_dir);
parser = EDGAR.parser(data_dir=data_dir)

tikrs = ["nflx"]

trainset = []


for tikr in tikrs:
    metadata.load_tikr_metadata(tikr)
    annotated_docs = parser.get_annotated_submissions(tikr)
    annotated_docs = [annotated_docs[0]]
    for doc in tqdm(annotated_docs, desc=f"Processing {tikr}", leave=False):
        fname = metadata.get_10q_name(tikr, doc)
        # Try load cached, otherwise regenerate new file
        features = parser.featurize_file(tikr, doc, fname,force = args.force) 
        features.sort_values(by=['page_number'])

        num_page = max(features.iloc[:]["page_number"], default=0)
    

        found_indices = np.unique([int(i) for i in features['found_index']])
        # Structure: Text str, Labels dict, labelled bool
        data = {i:{'text':None, 'labels':dict(), 'is_annotated':False, 'in_table':False, "page_number": 0 } for i in found_indices}
        page_texts = features[features["is_annotated"]== 1][["page_number", "page_text"]]
        page_texts = page_texts.drop_duplicates(subset = "page_number", keep = "last").set_index("page_number")
  
        for i in range(len(features)):
            i = features.iloc[i, :]
            d = data[i['found_index']]
            # Skip documents which are NOT annotated
            if i['in_table']:
                d['in_table'] = True
            if i['is_annotated']:
                d['is_annotated'] = True

            
        
            d['page_number'] = i["page_number"]
            if d['text'] is None:
                """
                x is a list with length of 2. Items in the list are:
                    1. value: the text value of the annotated label (e.g. 10-Q)
                    2. neighboring text: the text on the given page.
                y is a list with ['name', 'id', 'contextref', 'decimals', 'format', 'unitref'] tags
                """
                d['text'] = i['anno_text']

            d['labels'][i['anno_index']] = []
            for _attr in ['name', 'id', 'contextref', 'decimals', 'format', 'unitref']:
                d['labels'][i['anno_index']].append(i["anno_" + _attr])


        data_per_page = [ [] for i in range(num_page)]
        for i in data:
            #Only add annotated documents and non table label to trainset
            if not data[i]['is_annotated'] or data[i]['in_table']:
                continue; 
            d = data[i]
            
            # Data format: (x,y) where x refers to training features (present for unnannotated docs), and y refers to labels to predict
            data_per_page[d['page_number']-1].append((d['text'], d['labels'].values()))

        # Convert to list of [lists of tuples, page number, document,parent_company_tikr,text on that page] scheme where each list of tuples consists of all annotated webelements on that page
        for i , d in enumerate(data_per_page ):
            # Only add list if the list is not empty

            if len(d) == 0:
                continue
            trainset.append([ d, i+1,doc, tikr,page_texts.loc[i+1]["page_text"]  ])


"""
Training set structure:
Training set 
[   
    [ 
       list of tuples (x,y) 
       i.e [
            (x: anno_text, y:[list of labels]),
            ...
            (x: anno_text, y:[list of labels])
        ],
        page number,
        parent company tikr


    ],
    [...],
    ...
    ,
    [...]
]

"""
#print only one trainset
'''
   # Sample CSV with text, tag information
        with open(os.path.join('..','outputs','sample_data.csv'), 'w') as f:
            if len(trainset) > 0:
                text, labels = trainset[0]
                f.write(f"{text},{':'.join([str(i) for i in labels])}")
                for text, labels in trainset[1:]:
                    f.write(f"\n{text},{';'.join([str(i) for i in labels])}")
            else:
                warnings.warn('No Trainset Samples', RuntimeWarning)
'''

with open(os.path.join('..','outputs','sample_data_nflx.csv'), 'w') as f:
    for page in trainset: 
        f.write(f"Page_number: {page[1]},document:{page[2]},Tikr:{page[3]},Text:{page[4]}\n")
        data = page[0]
        text, labels = data[0]
        f.write(f"{text},{':'.join([str(i[0]) for i in labels])}")
        for text, labels in data[1:]:
            f.write(f"\n{text},{';'.join([str(i[0]) for i in labels])}")
        f.write(f"\n\n")
        