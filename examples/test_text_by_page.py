"""
Should work on Netflix 2013 10-Q

Opens a local 'nflx' 10-Q form (or tries)
Extracts 'text' elements from HTM tree
Visualizes elements by red border highlighting in firefox browser
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement 
import pandas as pd
import numpy as np


import itertools
from yaml import load, CLoader as Loader
import sys; sys.path.append('../')
import os
import pickle as pkl
import json


import EDGAR


# Hyperparameters
tikr = 'nflx'
submission_date = '20210101'
headless = True
data_dir = os.path.join('..','data')

# Set up
loader = EDGAR.dataloader(data_dir=data_dir, api_keys_path='../api_keys.yaml');
loader.metadata.load_tikr_metadata(tikr)

# Get nearest 10Q form path to above date
dname = loader.get_nearest_date_filename(submission_date, tikr)
fname = loader.metadata.get_10q_name(tikr, dname)

parser = EDGAR.parser(data_dir=data_dir, metadata=loader.metadata, headless=headless)

driver_path =  parser.get_driver_path(tikr, dname, fname)

########### testing for parse_text_by_page ##################

def Test_parse_text_by_page(parser):
    # Serializing json
    text = parser.parse_text_by_page()
    # Writing to sample.json
    with open(os.path.join("..", "outputs", "sample.json"), "w") as outfile:
        json.dump(text, outfile, default=lambda o: '<not serializable>', sort_keys=True, indent=4)

########### testing for get_annotation_feature ##################

data = None
if not os.path.exists(os.path.join('../data', 'parsed', tikr, f"{fname.split(',')[0]}.pkl")):
    print('Parsed Data does not exist... creating and caching')
    found, annotation_dict = parser._parse_annotated_text(driver_path)
    data = parser.parsed_to_data(found, annotation_dict, save=True, tikr=tikr, submission=dname)
    features = parser.get_annotation_features(found, annotation_dict, save=True, out_path=os.path.join('..','outputs','features.csv'))

else:
    print('Loading cached parsed data')
    data= parser.load_parsed(tikr, fname)
    
text_on = Test_parse_text_by_page(parser)
