"""
Should work on Netflix 2013 10-Q

Opens a local 'nflx' 10-Q form (or tries)
Extracts 'text' elements from HTM tree
Visualizes elements by red border highlighting in firefox browser
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd


import itertools
from yaml import load, CLoader as Loader
import os

# Absolute path of current python script directory
path = os.path.abspath(os.path.join(__file__, os.pardir))

apikeys = load( open(os.path.join(path,'../api_keys.yaml'),
                    'rb'), Loader=Loader)

# Two fields are necessary for EDGAR
#   The fields are the requester email and name
assert 'edgar_email' in apikeys, 'Set email';
assert 'edgar_agent' in apikeys, 'Set name of user';

data_dir = os.path.join(path, 'edgar_downloads/processed/')

tikr = 'nflx'

# Directory of current ticker
fpath = os.path.join(data_dir, f'{tikr}/')
# List of filing directories
files = os.listdir(fpath)
# Some document in some filed submission
f2 = os.listdir(os.path.join(fpath, files[0]))[0]

driver_path = "file:\/" + os.path.join(fpath, files[0], f2)

driver = webdriver.Firefox()
driver.get(driver_path)

found = driver.find_elements(By.TAG_NAME, 'font')

# Executes javascript in Firefox to make pretty borders around detected elements
def border(elem, driver):
    driver.execute_script(f"arguments[0].setAttribute(arguments[1], arguments[2])", elem, "style", "padding: 1px; border: 2px solid red; display: inline-block")


temp = [i for i in found if i.text not in set([' ', ''])]
for i in temp:
    border(i, driver);

#tables = [i.get_attribute('innerHTML') for i in driver.find_elements(By.TAG_NAME, 'table')]
