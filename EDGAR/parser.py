"""
Should work on Netflix 2013 10-Q

Opens a local 'nflx' 10-Q form (or tries)
Extracts 'text' elements from HTM tree
Visualizes elements by red border highlighting in firefox browser
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import numpy as np


import itertools
from yaml import load, CLoader as Loader
import os


from dataloader import edgar_dataloader

class edgar_parser:

    def __init__(self, headless: bool = True):
        fireFoxOptions = webdriver.FirefoxOptions()
        if headless:
            fireFoxOptions.add_argument("--headless")
        self.driver = webdriver.Firefox(options=fireFoxOptions)

    # dumps page source of driver at fpath
    def _save_driver_source(self, fpath: str) -> None:
        with open(fpath, 'w') as f:
            f.write(self.driver.page_source);
            
    """
        Javascript Helper Functions executed on Driver
            - border - draws color box around element
    """
    def _draw_border(self, elem, color: str = 'red'):
        self.driver.execute_script(
            f"arguments[0].setAttribute(arguments[1], arguments[2])",
            elem, "style",
            f"padding: 1px; border: 2px solid {color}; display: inline-block")

    """
    Parses some documents (2001-2013) at least

        driver_path -- path of file to open, or 'NONE' to keep current file
        highlight -- add red box around detected fields
        save -- save htm copy (with/without highlighting) to out_path
    """
    def parse_unannotated_text(self, driver_path: str, highlight: bool = False, save: bool = False, out_path: str = './sample.htm'):
        
        if driver_path is None:
            self.driver.get(driver_path)

        found = self.driver.find_elements(By.TAG_NAME, 'font')
        # Filter symbols using 'hashmap' set
        forbidden = {i for i in "\'\" (){}[],./\\-+^*`'`;:<>%#@$"}.union({'','**'})
        found = [i for i in found if i.text not in forbidden]

        # Executes javascript in Firefox to make pretty borders around detected elements
        if highlight:
            for i in found:
                self._draw_border(i, 'red');
        if save:
            self.save_driver_source(out_path)

        return found;

    """
    Parses some documents 2020+ at least

        driver_path -- path of file to open, or 'NONE' to keep current file
        highlight -- add red box around detected fields
        save -- save htm copy (with/without highlighting) to out_path
    """
    def parse_annotated_text(self, driver_path: str, highlight: bool = False, save: bool = False, out_path: str = './sample.htm'):
        
        if driver_path is not None:
            self.driver.get(driver_path)

        found = self.driver.find_elements(By.TAG_NAME, 'span')

        # Filter symbols using 'hashmap' set
        forbidden = {i for i in "\'\" (){}[],./\\-+^*`'`;:<>%#@$"}.union({'','**'})
        found = [i for i in found if i.text not in forbidden]

        annotation_dict = dict()
        for i in range(len(found)):
            found_annotation = found[i].find_elements(By.TAG_NAME, 'ix:nonnumeric')
            found_annotation += found[i].find_elements(By.TAG_NAME, 'ix:nonfraction')
            annotation_dict[found[i]] = found_annotation

        # Executes javascript in Firefox to make pretty borders around detected elements
        if highlight:
            for i in found:
                self._draw_border(i, 'red');
                for j in annotation_dict[i]:
                    self._draw_border(j, 'blue')

        if save:
            self._save_driver_source(out_path)

        return found, annotation_dict;

    """
    Parses some documents 2020+ at least

        driver_path -- path of file to open, or 'NONE' to keep current file
        highlight -- add red box around detected fields
        save -- save htm copy (with/without highlighting) to out_path
    """
    def parse_annotated_tables(self, driver_path: str, highlight: bool = False, save: bool = False, out_path: str = './sample.htm'):
        
        # If path is None, stay on current document
        if driver_path is not None:
            self.driver.get(driver_path)

        found_table = self.driver.find_elements(By.TAG_NAME, 'table')

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

                self._draw_border(found_table[i], 'green')
            elif table_is_numeric[i] == 1:
                self._draw_border(found_table[i], 'yellow')
            else:
                self._draw_border(found_table[i], 'pink')

        if save:
            self._save_driver_source(out_path)

        return found_table, table_is_numeric

    def __del__(self):
        self.driver.quit();

if __name__ == '__main__':
    
    # Hyperparameters
    tikr = 'nflx'
    submission_date = '20210101' #Find nearest AFTER this date

    headless = False

    # Set up
    loader = edgar_dataloader();
    loader.load_metadata(tikr)

    # Get nearest 10Q form path to above date
    dname = loader.get_nearest_date_filename(submission_date, tikr)
    fname = loader.get_10q_name(dname, tikr)
    driver_path = "file:\/" + os.path.join(loader.proc_dir, tikr, dname, fname)

    # Parsing
    parser = edgar_parser(headless=headless)
    found, annotation_dict = parser.parse_annotated_text(driver_path, highlight=True, save=False)
    tables, table_types = parser.parse_annotated_tables(driver_path=None, highlight=True, save=True, out_path='./sample.htm')

    temp = input('Press Enter to close  Window')
