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
import os
import pickle as pkl


from metadata_manager import metadata_manager
from dataloader import edgar_dataloader #for __main__

class edgar_parser:

    def __init__(self, metadata: metadata_manager = None,
                 data_dir: str = 'edgar_downloads',
                 headless: bool = True):

        fireFoxOptions = webdriver.FirefoxOptions()
        if headless:
            fireFoxOptions.add_argument("--headless")
        self.driver = webdriver.Firefox(options=fireFoxOptions)


        self.data_dir = data_dir

        if metadata is None:
            self.metadata = metadata_manager(data_dir=self.data_dir)
        else:
            self.metadata = metadata

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
            table_is_numeric[i] = 2

            # If a table has both non-numeric and non-fraction, the non-fraction takes precedence

            try:
                found_numeric = found_table[i].find_element(By.TAG_NAME, 'ix:nonfraction')
                table_is_numeric[i] = 0
                continue;

            except NoSuchElementException:
                pass;

            try:
                found_numeric = found_table[i].find_element(By.TAG_NAME, 'ix:nonnumeric')
                table_is_numeric[i] = 1

            except NoSuchElementException:
                pass;



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

    def load_parsed(self, tikr, submission):
        path = os.path.join(self.data_dir, 'parsed', tikr, submission.split('.')[0] + '.pkl')

        with open(path, 'rb') as f:
            return pkl.load(f)

    def get_annotation_info(self, elem: WebElement):
        return {'value': elem.text, 'name': elem.get_attribute('name'), 'id': elem.get_attribute('id')}


    def get_element_info(self, element: WebElement)-> list():
        return {"value": element.text,"location": element.location, "size": element.size}


    def parsed_to_data(self, webelements: list, annotations: dict,
            save: bool = False, out_path: str = None, keep_unlabeled=False):


        data = []
        for elem in webelements:
            tags = annotations[elem];

            if not keep_unlabeled and len(tags) == 0:
                continue;

            infos = []
            for tag in tags:
                infos.append(self.get_annotation_info(tag))
            data.append([self.get_element_info(elem), infos])

        if save:
            parse_dir = os.path.join(self.data_dir, 'parsed')
            out_path = os.path.join(parse_dir, out_path.split('.')[0] + '.pkl')

            if not os.path.exists(os.path.dirname(out_path)):
                os.system(f"mkdir -p {os.path.dirname(out_path)}")

            with open(out_path, 'wb') as f:
                pkl.dump(data, f)

        return data

    def __del__(self):
        self.driver.quit();

found = None
annotation_dict = None
parser = None
if __name__ == '__main__':

    # Hyperparameters
    tikr = 'nflx'
    submission_date = '20210101' #Find nearest AFTER this date

    headless = True

    # Set up
    loader = edgar_dataloader();
    loader.metadata.load_tikr_metadata(tikr)

    # Get nearest 10Q form path to above date
    dname = loader.get_nearest_date_filename(submission_date, tikr)
    fname = loader.get_10q_name(dname, tikr)
    driver_path = "file:\/" + os.path.join(loader.proc_dir, tikr, dname, fname)

    # Parsing
    parser = edgar_parser(metadata=loader.metadata, headless=headless)
    found, annotation_dict = parser.parse_annotated_text(driver_path, highlight=True, save=False)
    tables, table_types = parser.parse_annotated_tables(driver_path=None, highlight=True, save=True, out_path='./sample.htm')

    data = parser.parsed_to_data(found, annotation_dict, save=True, out_path=f"{tikr}/{fname}.pkl")
    #temp = input('Press Enter to close  Window')

    # Parsing
    parser = edgar_parser(headless=headless)
    found, annotation_dict = parser.parse_annotated_text(driver_path, highlight=True, save=False)
    tables, table_types = parser.parse_annotated_tables(driver_path=None, highlight=True, save=True, out_path='./sample.htm')
