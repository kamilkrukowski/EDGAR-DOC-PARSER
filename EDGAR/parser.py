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


from dataloader import edgar_dataloader

# Helper for Driver configurations
#   headless - Whether it appears as pop-up window
def get_driver(headless=True):
    fireFoxOptions = webdriver.FirefoxOptions()
    if headless:
        fireFoxOptions.add_argument("--headless")
    return webdriver.Firefox(options=fireFoxOptions)

# dumps page source of driver at fpath
def save_driver_source(driver, fpath):
    with open(fpath, 'w') as f:
        f.write(driver.page_source);
        
"""
    Javascript Helper Functions executed on Driver
        - border - draws color box around element
        - getPos - gets x,y coordinate of element
"""
def border(elem, driver, color='red'):
    driver.execute_script(f"arguments[0].setAttribute(arguments[1], arguments[2])", elem, "style", f"padding: 1px; border: 2px solid {color}; display: inline-block")

def getElemCoord(elem):
    return driver.execute_script(f"return arguments[0].getBoundingClientRect()", elem)

"""
Parses some documents (2001-2013) at least

    highlight -- add red box around detected fields
    save -- save htm copy (with/without highlighting) to out_path
"""
def parse(driver_path, highlight=False, save=False, out_path='./sample.htm'):
    
    driver.get(driver_path)

    found = driver.find_elements(By.TAG_NAME, 'font')
    # Filter symbols using 'hashmap' set
    forbidden = {i for i in "\'\" (){}[],./\\-+^*`'`;:<>%#@$"}.union({'','**'})
    found = [i for i in found if i.text not in forbidden]

    # Executes javascript in Firefox to make pretty borders around detected elements
    if highlight:
        for i in found:
            border(i, driver, 'red');
    if save:
        save_driver_source(driver, out_path)

    return found;


# Hyperparameters
tikr = 'nflx'
submission_date = '20050101' #Find nearest AFTER this date

headless = False
close = False;

# Set up
loader = edgar_dataloader();
loader.__load_metadata__(tikr)

dname = loader.get_nearest_date_filename(submission_date, tikr)
fname = loader.get_10q_name(dname, tikr)
driver_path = "file:\/" + os.path.join(loader.proc_dir, tikr, dname, fname)

# Parsing
driver = get_driver(headless=headless);
parsed = parse(driver_path, highlight=True, save=True, out_path='./sample.htm')

if close or headless:
    driver.quit();
