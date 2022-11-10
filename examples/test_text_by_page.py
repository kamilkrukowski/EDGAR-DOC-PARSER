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


from EDGAR import Metadata, parser, dataloader


# Hyperparameters
tikr = 'nflx'
#submission_date = '20210101' #Find nearest AFTER this date
submission_date = '20070101'
headless = True

# Set up
loader = dataloader(data_dir='../data/',api_keys_path ='../api_keys.yaml');
loader.metadata.load_tikr_metadata(tikr)

# Get nearest 10Q form path to above date
dname = loader.get_nearest_date_filename(submission_date, tikr)
fname = loader.metadata.get_10q_name(tikr, dname)
driver_path = "file:\/" + os.path.join(loader.proc_dir, tikr, dname, fname)
print(driver_path)
parser = parser(metadata=loader.metadata, headless=headless)


########### testing for parse_text_by_page ##################

def Test_parse_text_by_page(parser):
    # Serializing json
    text = parser.parse_text_by_page()
    # Writing to sample.json
    with open("sample.json", "w") as outfile:
        json.dump(text, outfile, default=lambda o: '<not serializable>',sort_keys=True, indent=4)

########### testing for get_annotation_feature ##################
def Test_get_annotation_features(found, annotation_dict):
	parser.get_annotation_features(found, annotation_dict,save= True, out_path=  'sample.csv')

# Parsing
data = None
if not os.path.exists(os.path.join('../data', 'parsed', tikr, f"{fname.split(',')[0]}.pkl")):
    print('Parsed Data does not exist... creating and caching')
    if(int(submission_date) > 20200101):
    	found, annotation_dict = parser._parse_annotated_text(driver_path, highlight=False, save=False)
    	Test_get_annotation_features(found, annotation_dict)
    else:
    	found = parser._parse_unannotated_text(driver_path, highlight=False, save=True)

else:
    print('Loading cached parsed data')
    data= parser.load_parsed(tikr, fname)
    
Test_parse_text_by_page(parser)
