"""
    This file will downloads and parses financial data from the SEC EDGAR database for a list of companies specified in the "tickers.txt" file. 
    TThe data is then processed and saved as a tokenizer and raw data file in the current directory.
"""

import os
import time
import itertools
import argparse
import sys; 
#sys.path.append('..')


from tqdm.auto import tqdm
from secedgar import FilingType
from transformers import BertTokenizerFast
import numpy as np
import torch


import EDGAR



# Command line magic for common use case to regenerate dataset
#   --force to overwrite outdated local files
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--force', action='store_true')
parser.add_argument('-nflx', '--demo', action='store_true')
args = parser.parse_args()

data_dir = os.path.join("..","data")
loader = EDGAR.downloader(data_dir=data_dir);
metadata = EDGAR.metadata(data_dir=data_dir)
parser = EDGAR.parser(data_dir=data_dir)


# List of companies to process
tikrs = open(os.path.join("..", 'tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]
if args.demo:
    tikrs = ['nflx']

for tikr in tikrs:
    loader.metadata.load_tikr_metadata(tikr)

def download_tikrs(tikrs):
    to_download = [];
    if args.force:
        print(f"Forcing Downloads...")
        for tikr in tikrs:
            to_download.append(tikr)
    else:
        # Download missing files
        for tikr in tikrs:
            if not loader._is_downloaded(tikr):
                to_download.append(tikr)

    if len(to_download) != 0:
        for tikr in tqdm(to_download, desc="Downloading", leave=False):
            loader.query_server(tikr, force=args.force, filing_type=FilingType.FILING_10Q)
            time.sleep(5)

def change_digit_to_alphanumeric(text):
        for alph in '0123456789':
            text = text.replace(alph, f" [ALPHANUMERIC] ")
        return text

download_tikrs(tikrs);

raw_data = list();
label_map = set();
for tikr in tikrs:
    # Unpack downloaded files into relevant directories
    loader.unpack_bulk(tikr, loading_bar=True, force = args.force, complete = False , document_type = "10-Q", desc=f"{tikr} :Inflating HTM")
    annotated_docs = parser.get_annotated_submissions(tikr, silent=True)

    if(args.demo):
        annotated_docs = [annotated_docs[0]]

    # to process the documents and extract relevant information. 
    for doc in annotated_docs:
        fname = metadata.get_10q_name(tikr, doc)
        features = parser.featurize_file(tikr, doc, fname,force = args.force, silent=True) 
        found_indices = np.unique([int(i) for i in features['found_index']])
        # Structure: Text str, Labels dict, labelled bool
        data = {i:{'text':None, 'labels':dict(), 'is_annotated':False, 'in_table':False, "page_number": 0 } for i in found_indices}
        
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
                d['text'] = i['span_text']

            if i['anno_index'] is not None:
                d['labels'][i['anno_index']] = []
                for _attr in ['name', 'id', 'contextref', 'decimals']:
                    d['labels'][i['anno_index']].append(i["anno_" + _attr])

        doc_data = []
        for i in data:
            # This checks for the all the element on a page. Only add element that has labels to the training set.
            if data[i]['in_table']:
                continue 
            if not data[i]['is_annotated']:
                continue
            d = data[i]
            labels = list(d['labels'].values())
        
            for label in labels:
                label_map = label_map.union({label[0]})


            # Data format: (x,y) where x refers to training features (present for unnannotated docs), and y refers to labels to predict
            doc_data.append((d['text'], labels))
  
        raw_data.append([doc_data,  doc, tikr ])

label_map = {y:i for i,y in enumerate(label_map)}

#### SETTINGS
MAX_SENTENCE_LENGTH = 200
PREPROCESS_PIPE_NAME = 'DEFAULT'
SPARSE_WEIGHT = 0.5
MIN_OCCUR_PERC = 0
MIN_OCCUR_COUNT = 20


#### saves the raw data
vocab_dir = os.path.join(metadata.data_dir, "dataloader_cache")
out_dir = os.path.join(vocab_dir, PREPROCESS_PIPE_NAME);
if not os.path.exists(out_dir):
    if not os.path.exists(vocab_dir):
        os.mkdir(vocab_dir)
    os.mkdir(out_dir);
np.savetxt(os.path.join(out_dir, 'all_possible_labels.txt'), [key for key in label_map], fmt="%s")

# i is the data in document
# j is the (text, list of list labels)
# k is the list of list labels
label_data = [k[0] for k in itertools.chain.from_iterable([j[1] for j in itertools.chain.from_iterable([i[0] for i in raw_data])])]
all_labels_count = len(label_data)
all_labels, counts = np.unique(label_data, return_counts=True)
reindexing = list(reversed(np.argsort(counts)))
# Create a dictionary of words and their counts
label_counts = dict(zip(all_labels[reindexing], counts[reindexing]))
# Create a list of words that meet the criteria
selected_labels = [label for label, count in label_counts.items() if count >= MIN_OCCUR_COUNT and count/all_labels_count >= MIN_OCCUR_PERC]

# Remove all company specific systems predicted
kept_systems = {'dei', 'us-gaap'}
selected_labels = [i for i in selected_labels if i.split(':')[0] in kept_systems]
np.savetxt(os.path.join(out_dir, 'labels.txt'), [label for label in selected_labels], fmt="%s")
        

# Define your text data
text_data = [change_digit_to_alphanumeric(i[0]) for i in itertools.chain.from_iterable([i[0] for i in raw_data])]
tokenizer = BertTokenizerFast.from_pretrained('bert-large-cased')
#Define new special token for digit 
new_special_tokens = ["[ALPHANUMERIC]"]

tokenizer = tokenizer.train_new_from_iterator(text_iterator=text_data, vocab_size=10000,new_special_tokens = new_special_tokens )

# Save the trained tokenizer
tokenizer.save_pretrained(out_dir);

# Embed all sentences, create label vectors, create loss weight masks
inputs = []
num_labels = len(selected_labels);
label_map = {y:i+1 for i,y in enumerate(selected_labels)}
pos_weights = None;
neg_weights = None;
for document in raw_data:
    elems, doc_id, tikr = document;
    for elem in elems:
        inputs.append(tokenizer(elem[0], return_tensors='pt', truncation=True))
        inputs[-1]["y"] = torch.zeros(num_labels+1).float(); #Extra one for unknown label
        num_labelled = 0;
        pos_weights = torch.zeros(num_labels+1).float()
        neg_weights = torch.ones(num_labels+1).float()
        
        for label in elem[1]:
            label_idx = label_map.get(label[0], 0)
            if pos_weights[label_idx] == 1:
                continue;
            pos_weights[label_idx] = 1
            neg_weights[label_idx] = 0
            inputs[-1]["y"][label_idx] = 1
            
            num_labelled = num_labelled + 1
        
        pos_weights = pos_weights * (1-SPARSE_WEIGHT) / num_labelled
        neg_weights = neg_weights * (SPARSE_WEIGHT) / (num_labels + 1 - num_labelled)
        inputs[-1]["loss_mask"] = pos_weights + neg_weights

