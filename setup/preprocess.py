"""
    This file will downloads and parses financial data from the SEC EDGAR database for a list of companies specified in the "tickers.txt" file. 
    TThe data is then processed and saved as a tokenizer and raw data file in the current directory.
"""

import os
import time
import itertools
import argparse
import sys; 
sys.path.append('..')


from tqdm.auto import tqdm
from secedgar import FilingType
from transformers import FastBertTokenizer
import EDGAR



# Command line magic for common use case to regenerate dataset
#   --force to overwrite outdated local files
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--force', action='store_true')
parser.add_argument('-nflx', '--demo', action='store_true')
args = parser.parse_args()

data_dir = "data"
loader = EDGAR.downloader(data_dir=data_dir);
metadata = EDGAR.metadata(data_dir=data_dir)
parser = EDGAR.parser(data_dir=data_dir)



# List of companies to process
tikrs = open(os.path.join(loader.path, 'tickers.txt')).read().strip()
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

download_tikrs(tikrs);

raw_data = list();
label_map = set();
for tikr in tikrs:
    # Unpack downloaded files into relevant directories
    loader.unpack_bulk(tikr, loading_bar=True, force = args.force, desc=f"{tikr} :Inflating HTM")
    annotated_docs = parser.get_annotated_submissions(tikr, silent=True)

    if(args.demo):
        annotated_docs = [annotated_docs[0]]

    # to process the documents and extract relevant information. 
    for doc in annotated_docs:
        fname = metadata.get_10q_name(tikr, doc)
        features = parser.featurize_file(tikr, doc, fname,force = args.force, silent=True) 

        features.sort_values(by=['page_number'],ascending = True, inplace = True)
        num_page = max(features.iloc[:]["page_number"],default = 0)

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
                for _attr in ['name', 'id', 'contextref', 'decimals', 'format', 'unitref']:
                    d['labels'][i['anno_index']].append(i["anno_" + _attr])

        data_per_page = [ [] for _ in range(num_page)]
        for i in data:
            # This checks for the all the element on a page. Only add element that has labels to the training set.
            if data[i]['in_table']:
                continue 
            if not data[i]['is_annotated']:
                continue
            d = data[i]
            
            # Data format: (x,y) where x refers to training features (present for unnannotated docs), and y refers to labels to predict
            data_per_page[d['page_number']-1].append((d['text'], list(d['labels'].values())))

        #Convert to list of [lists of tuples, page number, document, parent_company_tikr] scheme where each list of tuples consists
        # of all annotated webelements on that page
        for i , d in enumerate(data_per_page ):
            # Only add list if the list is not empty
            if len(d) == 0:
                continue
            raw_data.append([d, i+1, doc, tikr ])
            for elem in d:
                for label in elem[1]:
                    label_map = label_map.union({label[0]})
        
label_map = {y:i for i,y in enumerate(label_map)}

#### SETTINGS
MAX_SENTENCE_LENGTH = 200
PREPROCESS_PIPE_NAME = 'DEFAULT'


#### saves the raw data
vocab_dir = os.path.join(metadata.data_dir, "dataloader_cache")
out_dir = os.path.join(vocab_dir, PREPROCESS_PIPE_NAME);
if not os.path.exists(out_dir):
    if not os.path.exists(vocab_dir):
        os.mkdir(vocab_dir)
    os.mkdir(out_dir);
np.savetxt(os.path.join(out_dir, 'labels.txt'), [key for key in label_map], fmt="%s")


# Save the trained tokenizer to a file
tokenizer = BertTokenizerFast.from_pretrained('bert-large-cased')

# Define your text data
text_data = [i[0] for i in itertools.chain.from_iterable([i[0] for i in raw_data])]

tokenizer = tokenizer.train_new_from_iterator(text_iterator=text_data, vocab_size=10000)
# Save the trained tokenizer to a file
tokenizer.save_pretrained(os.path.join(vocab_dir, "wordpiece"));