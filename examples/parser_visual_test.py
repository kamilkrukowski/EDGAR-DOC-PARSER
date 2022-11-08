"""
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
import os
import pathlib
import pickle as pkl
import sys ; sys.path.append('../')


import EDGAR


# Hyperparameters
tikr = 'nflx'
submission_date = '20210101' #Find nearest AFTER this date
headless = False

# Set up
loader = EDGAR.dataloader(data_dir='../data', api_keys_path='../api_keys.yaml');
loader.metadata.load_tikr_metadata(tikr)

# Get nearest 10Q form path to above date
dname = loader.get_nearest_date_filename(submission_date, tikr)
fname = loader.get_10q_name(dname, tikr)
driver_path = pathlib.Path(os.path.join(loader.proc_dir, tikr, dname, fname)).as_uri()

parser = EDGAR.parser(metadata=loader.metadata, headless=headless)

# Parsing
data = None
if not os.path.exists(os.path.join('..', 'edgar_downloads', 'parsed', tikr, f"{fname.split(',')[0]}.pkl")):
    print('Parsed Data does not exist... creating and caching')

    found, annotation_dict = parser.parse_annotated_text(driver_path, highlight=True, save=False)
    parser.get_annotation_features(found, annotation_dict,save = True)
    input("enter to continue")

    data = parser.parsed_to_data(found, annotation_dict, save=True, out_path=f"{tikr}/{fname}.pkl")
else:
    print('Loading cached parsed data')
    data= parser.load_parsed(tikr, fname)

print(f'Saving sample data to \'outputs/sample_data.txt\'')
if not os.path.exists(os.path.join('..','outputs')):
    os.system('mkdir -p ../outputs')
with open(os.path.join('..', 'outputs', 'sample_data.txt'), 'w') as f:
    for i in data:
        f.write(i[0]['value'])
        f.write('\t')
        f.write(i[1][0]['name'])
        for j in i[1][1:]:
            f.write(',')
            f.write(j['name'])
        f.write('\n')
