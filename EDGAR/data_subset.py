#from torchtext.vocab import build_vocab_from_iterator
import torch
import numpy as np
from tqdm.auto import tqdm

import pickle as pkl
import os


from .metadata_manager import metadata_manager
from transformers import BertTokenizerFast


"""
    Constructor: (data_dir)
"""
class DataSubset():
    

    def __init__(self, tikrs, metadata, parser, **kwargs):
        #super(Dataset).__init__()

        self.metadata = metadata
        self.parser = parser

      
        self.raw_data= []

        if type(tikrs) is str:
            tikrs = [tikrs];
            self.tikrs = tikrs

        for tikr in tqdm(tikrs, desc=f"Preprocessing Documents", leave=False):
            self.metadata.load_tikr_metadata(tikr)
            annotated_docs = self.parser.get_annotated_submissions(tikr)

            for doc in annotated_docs:

                fname = metadata.get_10q_name(tikr, doc)
                # Try load cached, otherwise regenerate new file
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

                
                for i in data:
                    # This checks for the all the element on a page. Only add element that has labels to the training set.
                    if data[i]['in_table']:
                        continue
                    if not data[i]['is_annotated']:
                        continue
                    d = data[i]

                    #print([ i[0] for i in d['labels'].values()])
                    self.raw_data.append([d['text'], [ i[0] for i in d['labels'].values()],d['page_number'],doc,tikr])
                    #np.save("raw_data.npy", RAW_DATA)


    def save_raw_data(self, fname = "raw_data.npy"):
    	np.save( fname, np.array(self.raw_data,dtype = object))


    def label_frequency(self,data = None,min_percent = 0.0, min_occurence = 1):
        """
            calculate the frequency of each label in the given data and return a list of valid labels and a dictionary of label counts.

            Parameters
            ---------
            data: list
                The input data that the function will operate on. If no data is provided, the function will use self.raw_data instead.
            min_occurrence: integer
                the method creates a list of valid labels that meet the criteria of having a count greater than or equal to min_occurrence.
            min_percent: Double
                 the method creates a list of valid labels that meet the criteria of having a percentage of the total data greater than or equal to min_percent.
        """
        labels = []
        if data == None:
            data = self.raw_data
        # Extract labels from the data
        for _, label, _, _, _ in self.raw_data:
            labels += label
   
        # Calculate label frequencies
        labels, counts = np.unique(labels, return_counts=True)
        # Create a dictionary of labels and their counts
        label_counts = dict(zip(labels, counts))
        # Create a list of labels that meet the criteria
        valid_labels = [label for label, count in label_counts.items() if count >= min_occurence and count/len(self.raw_data) >= min_percent]
        return valid_labels, label_counts


    def subset(self, data = None, labels = None, tikrs= None, save = False,keywords = None, fname = "subset.npy", all_keywords = False):
        """
            takes in several parameters and returns a subset of the input data based on certain conditions.

            Parameters
            ---------
            data: list
                The input data that the function will operate on. If no data is provided, the function will use self.raw_data instead.
            labels: list
                a list of labels that the function will use to filter the data. If provided, the function will keep only those data points that have at least one label in this list.
            tikrs: list
                a list of tikr names that the function will use to filter the data. If provided, the function will keep only those data points that have a tikr name in this list.
            save: boolean
                a boolean value that indicates whether the filtered data should be saved to a file.
            keywords: list
                a list of keywords that the function will use to filter the data. If provided, the function will keep only those data points that have at least one keyword in this list.
            fname: str
                the name of the file to which the filtered data will be saved, if save is set to True.
            all_keywords: boolean
                a boolean value that indicate whether the filtered data should contain all the keywords provided or at least one. 
        """
        if data == None:
            data = self.raw_data
        
        subset_data = data
        if labels != None and len(labels) > 0:
            #print(subset_data ,"\n\n")
            subset_data = [d for d in subset_data if any(label in labels for label in d[1])] 
        if tikrs != None and len(tikrs) > 0:
            subset_data = [d for d in subset_data if d[4] in tikrs ]
        if keywords != None and len(keywords) > 0:
            if all_keywords:
                subset_data = [d for d in data if  all(keyword in keywords for keyword in d[0])]
            else:
                subset_data = [d for d in data if  any(keyword in keywords for keyword in d[0])]


        if save:
            np.save(fname, np.array(subset_data, dtype=object))
        return subset_data

    def load_stopword(self, data_path = None):
        if data_path == None:
            data_path = os.path.join(self.metadata.path, "stop_word.npy" )
        return np.load(data_path)

    def word_frequency(self,data = None,min_percent = 0.0, min_occurence = 1):
        all_words= []
        stop_words = self.load_stopword() 

        if data == None:
            data = self.raw_data

        # Extract words from the data
        for text, _, _, _, _ in self.raw_data:
            for p in '.!,;:\'\"()@#$%&/+=-*“”’—':
                text = text.replace(p, '')
            for alph in '0123456789':
                text = text.replace(alph, f" <alphanumeric> ")


            words = text.split(" ")
            words = [word for word in words if word != "" and word.lower() not in stop_words ]
            
            all_words += words
      
        all_words_count = len(all_words)
        # Calculate word frequencies
        words, counts = np.unique(all_words, return_counts=True)
        # Create a dictionary of words and their counts
        word_counts = dict(zip(words, counts))
        # Create a list of words that meet the criteria
        valid_words = [word for word, count in word_counts.items() if count >= min_occurence and count/all_words_count >= min_percent]
        return valid_words, word_counts

    def change_digit_to_alphanumeric(self, text):
        for alph in '0123456789':
            text = text.replace(alph, f" ["+str(alph)+"/ALPHANUMERIC] ")
        return text

    def build_tokenizer(self, pretrained = None,data = None, vocab_size = 300000,save = False, alphanumeric = True):

        if pretrained == None:
            if data == None:
                data = self.raw_data
            # Create the tokenizer
            tokenizer = BertTokenizerFast.from_pretrained('bert-large-cased')

            

            
            if alphanumeric:
                # Define your text data
                text_data = [self.change_digit_to_alphanumeric(text) for text, _, _, _, _ in data]
                
                new_special_tokens = ["["+str(alph)+"/ALPHANUMERIC]" for alph in '0123456789']
                tokenizer = tokenizer.train_new_from_iterator(text_data,vocab_size,new_special_tokens= new_special_tokens)
            else: 
                # Define your text data
                text_data = [text for text, _, _, _, _ in data]
                tokenizer = tokenizer.train_new_from_iterator(text_data,vocab_size)
        else:
            tokenizer = BertTokenizerFast.from_pretrained(pretrained)

        # Save the trained tokenizer to a file
        if save:
            tokenizer.save_pretrained("bert_tokenizer_fast")

        return tokenizer

    def generate_dataset(self, data = None, tokenizer = None, save = False, fname_x = "x_data", fname_y = "y_data"):
        if data == None:
            data = self.raw_data


        if save:
            data_path_x = os.path.join(self.metadata.path, fname_x )
            np.save(data_path_x, np.array(data[0], dtype=object))
            data_path_y = os.path.join(self.metadata.path, fname_y )
            np.save(data_path_y, np.array(data[1], dtype=object))
        return data[0],  data[1]




