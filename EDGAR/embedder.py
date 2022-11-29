"""
Embedder class embeds phrases and returns vectors for machine learning processing
"""
import pandas as pd

import gensim
from gensim.models import Word2Vec
from gensim.test.utils import common_texts

import numpy as np

import re
import string
import nltk
from nltk.stem import PorterStemmer
import heapq


import torch
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from pytorch_pretrained_bert import BertTokenizer, BertConfig
from pytorch_pretrained_bert import BertAdam, BertForSequenceClassification



# types: BoW, Word2Vec, BERT
class embedder:
    def __init__(self, type='BagOfWords', MAX_LEN=100):
        
        self.type = type
        self.MAX_LEN = MAX_LEN
        
        if type == 'Word2Vec':
            pretrained_embeddings_path = 'GoogleNews-vectors-negative300.bin'
            self.model = gensim.models.KeyedVectors.load_word2vec_format(pretrained_embeddings_path,  binary=True)
        elif type == 'BagOfWords':
            self.model = None
            self.dictionary = {}
        elif type == 'BERT':
            self.model = None
            
    
    
    def clean_phrase(self, text, stem=None):
        final_string = ""
        text = text.lower()
        
        """ removes non-alpha characters and keeps whitespace """
        text = re.sub(r'[^A-Za-z0-9 ]', '', text)
        text = text.split(' ')
        
        stopwords = nltk.corpus.stopwords.words("english")
        # removes stop words and empty strings
        text_filtered = [word for word in text if not word in stopwords and word != '']
        if stem == 'Stem':
            stemmer = PorterStemmer() 
            text_stemmed = [stemmer.stem(word) for word in text_filtered]
        else: 
            text_stemmed = text_filtered
            
        final_string = ' '.join(text_stemmed)
        return final_string

    
    # only for Bagofwords
    def add_dictionary(self, phrase):
        
        for word in phrase.split(' '):
            if word not in self.dictionary.keys():
                self.dictionary[word] = 1
            else:
                self.dictionary[word] += 1
                
     



    
    def embed_phrase(self, phrase):
        if self.type == 'Word2Vec':
            temp = []
            bad_words =[]
            for word in phrase.split(' '):
                try:
                    word_vec = self.model[word]
                    temp.append(word_vec)
                except:
                    pass
            element_vec = np.mean(np.array(temp), axis=0)
            return element_vec
        
        elif self.type == 'BagOfWords':
            freq_words = heapq.nlargest(500, self.dictionary, key=self.dictionary.get)
            element_vec = []
            for word in phrase.split(' '):
                if word in freq_words:
                    element_vec.append(1)
                else:
                    element_vec.append(0)
            element_vec = np.array(element_vec)
            element_vec = np.pad(element_vec, pad_width=(0, self.MAX_LEN-len(element_vec)), mode='constant')
            return element_vec
            
        elif self.type == 'BERT':
            tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', do_lower_case=True)
            tokenized_texts = tokenizer.tokenize(phrase)
            element_vec = tokenizer.convert_tokens_to_ids(tokenized_texts)
            element_vec = np.pad(element_vec, pad_width=(0, self.MAX_LEN-len(element_vec)), mode='constant')
            return element_vec
            

    
