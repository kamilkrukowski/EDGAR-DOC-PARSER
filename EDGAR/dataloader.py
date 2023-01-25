from torch.utils.data import Dataset
import torch
import numpy as np
from tqdm.auto import tqdm


import pickle as pkl
import os
import re


from .metadata_manager import metadata_manager


"""
    Constructor: (data_dir)
"""
class EDGARDataset(Dataset):
    def __init__(self, tikrs, metadata, parser, **kwargs):
        super(Dataset).__init__()

        self.metadata = metadata
        self.parser = parser

        raw_data = []
        self.x = []
        self.y = []

        if type(tikrs) is str:
            tikrs = [tikrs];

        for tikr in tqdm(tikrs, desc=f"Preprocessing Documents", leave=False):
            self.metadata.load_tikr_metadata(tikr)
            annotated_docs = self.parser.get_annotated_submissions(tikr)
            
            for doc in annotated_docs:
            
                fname = metadata.get_10q_name(tikr, doc)
                # Try load cached, otherwise regenerate new file
                assert self.metadata.file_was_processed(tikr, doc, fname)
                features = self.parser.featurize_file(tikr, doc, fname,force = kwargs.get('force', False)) 
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
                    raw_data.append([ d, i+1,doc, tikr ])
        
        # Max sentence length
        self.max_sentence_len = kwargs.get('max_sentence_len', None)
        if (self.max_sentence_len is None):
            kwargs['calc_max_token_len'] = True;
            self.max_sentence_len = 2 #For start, stop tokens, we add 2 more to running total

        # Generate Vocabulary
        self.vocab = set()
        self.labels = set()
        self._len = 0
        for page in raw_data:
            elems, page_number, doc_id, tikr = page;
            for elem in elems:
                tokens = self.tokenize(elem[0])
                if kwargs.get('calc_max_token_len', False):
                    self.max_sentence_len = max(self.max_sentence_len, len(tokens))
                self.vocab = self.vocab.union(tokens);
                self._len += 1;
                for label in elem[1]:
                    self.labels = self.labels.union({label[0]})
        
        self.labels = {y:i+1 for i,y in enumerate(self.labels)}
        self.first_vocab_token = 5
        self.vocab = {y:i+self.first_vocab_token for i,y in enumerate(self.vocab)}

        #Label embedding
        num_labels = len(self.labels);
        if kwargs.get('debug', False):
            print(f"Number of labels: {num_labels}")
            print(f"Max sentence length is {self.max_sentence_len}")
         
        for page in raw_data:
            elems, page_number, doc_id, tikr = page;
            for elem in elems:
                self.x.append(self.embed(elem[0]))
                self.y.append(torch.zeros(num_labels+1).float()); #Extra one for unknown label
                for label in elem[1]:
                    label_idx = self.labels.get(label[0], 0) 
                    self.y[-1][label_idx] = 1
        
        #Categorical Embedding        


        
    def __len__(self):
        return self._len

    def __getitem__(self, idx):
        x = self.x[idx]
        y = self.y[idx]
        return (x, y)

    def tokenize(self, sentence):
        punctuation = '.!,;:\'\"()@#$%&/+=-'
        for ch in punctuation:
            sentence.replace(ch, f" {ch} ")
        for alph in '0123456789':
            sentence.replace(alph, f" <alphanumeric> ")

        return sentence.split(' ')


    def embed(self, sentence: str):
            first_token = 5;

            pad_token = 0
            unk_token = 1
            start_token = 2
            end_token = 3
            tokens = self.tokenize(sentence);

            out = torch.zeros(self.max_sentence_len).long();

            out[0] = start_token; idx = 1
            for token in tokens:
                if (token == ''): 
                    continue;
                if (idx == self.max_sentence_len-2):
                    break;
                token_id = self.vocab.get(token, unk_token)
                out[idx] = token_id
                idx += 1;
            out[idx] = end_token
            return out
