import pandas as pd

from dataloader import edgar_dataloader
from parser import edgar_parser

import gensim
from gensim.models import Word2Vec
from gensim.test.utils import common_texts

import numpy as np

import re
import string
import nltk
from nltk.stem import PorterStemmer



class embedder:
    def __init__(self,
                 pretrained_embeddings_path = 'GoogleNews-vectors-negative300.bin'):
        
        self.model = gensim.models.KeyedVectors.load_word2vec_format(pretrained_embeddings_path,  binary=True)
    
    
    def clean_phrase(self, text, stem=None):
        final_string = ""
        text = text.lower()
        text = re.sub('[^A-Za-z0-9]+', ' ', text)
        text = text.split(' ')
        
        stopwords = nltk.corpus.stopwords.words("english")
        text_filtered = [word for word in text if not word in stopwords]
        
        if stem == 'Stem':
            stemmer = PorterStemmer() 
            text_stemmed = [stemmer.stem(word) for word in text_filtered]
        else: 
            text_stemmed = text_filtered
            
        final_string = ' '.join(text_stemmed)
        return final_string


    
    def embed_phrase(self, phrase):
        temp = []
        bad_words =[]
        for word in phrase.split(' '):
            try:
                word_vec = self.model[word]
                temp.append(word_vec)
            except:
                bad_words.append(word)
        element_vec = np.mean(np.array(temp), axis=0)
        return element_vec, bad_words
        


embedder = embedder()
cleaned_phrase = embedder.clean_phrase('hello, my name is Kelsey ihjdfajaf ! ajflaj and I like sushi!')
vec, bad_words = embedder.embed_phrase(cleaned_phrase)
print(vec) 
print(bad_words)
        
        
