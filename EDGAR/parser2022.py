from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import numpy as np
from selenium.common.exceptions import NoSuchElementException


import itertools
import base64
import os


from dataloader import edgar_dataloader


loader = edgar_dataloader();
path = loader.path;
args = loader.apikeys;

tikr = 'nflx'
loader.__load_metadata__(tikr)

# Find nearest submission AFTER this date
dname = loader.get_nearest_date_filename('20200101', tikr)
fname = loader.get_10q_name(dname, tikr)

driver_path = "file:\/" + os.path.join(loader.proc_dir, tikr, dname, fname)

driver = webdriver.Firefox()

driver.get(driver_path)

found_text = driver.find_elements(By.TAG_NAME, 'span')
# found_annotation = driver.find_elements(By.TAG_NAME, 'ix:nonnumeric')
temp_txt = [i for i in found_text if i.text not in set([' ', ''])]
annotation_dict = dict()
# have_annotation = np.zeros_like(temp_txt, 'bool')
# elements_with_annotation = []
for i in range(len(temp_txt)):
    found_annotation = temp_txt[i].find_elements(By.TAG_NAME, 'ix:nonnumeric')
    found_annotation += temp_txt[i].find_elements(By.TAG_NAME, 'ix:nonfraction')
    # if len(found_annotation) != 0:
        # have_annotation[i] = True
        # elements_with_annotation += [temp_txt[i]]
    annotation_dict[temp_txt[i]] = found_annotation

# temp_anno = [i for i in found_annotation if i.text not in set([' ', ''])]

def border(elem, driver, color='red'):
    driver.execute_script(f"arguments[0].setAttribute(arguments[1], arguments[2])", elem,
                          "style", f"padding: 1px; border: 2px solid {color}; display: inline-block")

for i in temp_txt:
    border(i, driver, 'red');
for i in annotation_dict:
    for j in annotation_dict[i]:
        border(j, driver, 'blue')


found_table = driver.find_elements(By.TAG_NAME, 'table')


table_is_numeric = np.zeros_like(found_table, 'int')# 0: numerical, 1: non-numerical, 2: unannotated
for i in range(len(found_table)):
    try:
        found_numeric = found_table[i].find_element(By.TAG_NAME, 'ix:nonfraction')
        table_is_numeric[i] = 0
    except NoSuchElementException:
        try:
            found_numeric = found_table[i].find_element(By.TAG_NAME, 'ix:nonnumeric')
            table_is_numeric[i] = 1
        except NoSuchElementException:
            table_is_numeric[i] = 2

for i in range(len(found_table)):
    if table_is_numeric[i] == 0:

        border(found_table[i], driver, 'green')
    elif table_is_numeric[i] == 1:
        border(found_table[i], driver, 'yellow')
    else:
        border(found_table[i], driver, 'pink')
