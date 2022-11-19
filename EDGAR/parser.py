from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement 
import pandas as pd
import numpy as np


import warnings
import os
import pickle as pkl
import re
import pathlib


from .metadata_manager import metadata_manager


class edgar_parser:
    """
        Main class for extracting information from HTML documents
    
    """

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
    def _parse_unannotated_text(self, driver_path: str, 
                                highlight: bool = False, save: bool = False, out_path: str = os.path.join('.','sample.htm')):
        
        if driver_path is not None:
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
            self._save_driver_source(out_path)

        return found;

    """
        Get a driver filename uri path from data identifiers
    """
    def get_driver_path(self, tikr, submission, fname, partition='processed'):
        return pathlib.Path(os.path.join(self.data_dir, partition, tikr, submission, fname)).absolute().as_uri()

    def _parse_annotated_text(self, driver_path: str, highlight: bool = False, save: bool = False, out_path: str = os.path.join('.','sample.htm')):
        """
        Parses some documents 2020+ at least

            driver_path -- path of file to open, or 'NONE' to keep current file
            highlight -- add red box around detected fields
            save -- save htm copy (with/without highlighting) to out_path
        """
        
        if driver_path is not None:
            self.driver.get(driver_path)

        found = self.driver.find_elements(By.TAG_NAME, 'span')

        # Filter symbols using 'hashmap' set
        forbidden = {i for i in "\'\" (){}[],./\\-+^*`'`;:<>%#@$"}.union({'','**'})
        found = [i for i in found if i.text not in forbidden]

        
        in_table = np.zeros(len(found), dtype=bool)

        annotation_dict = dict()
        for i in range(len(found)):
            
            found_annotation = found[i].find_elements(By.TAG_NAME, 'ix:nonnumeric')
            found_annotation += found[i].find_elements(By.TAG_NAME, 'ix:nonfraction')
            
            current_element = found[i]
            while True: # loop through ancestors
                # # check if current is root
                parent = self.driver.execute_script("return arguments[0].parentNode", current_element)
                if parent.tag_name == 'body': # This is the 'root' of an html tree
                    break;
                if current_element.tag_name == 'table':
                    in_table[i] = True
                    break
                current_element = parent
            
            annotation_dict[found[i]] = found_annotation
        # Executes javascript in Firefox to make pretty borders around detected elements
        if highlight:
            for i in found:
                self._draw_border(i, 'red');
                for j in annotation_dict[i]:
                    self._draw_border(j, 'blue')

        if save:
            self._save_driver_source(out_path)

        return found, annotation_dict, in_table;

    """
        Return list of submissions names with annotated 10-Q forms
    """
    def get_annotated_submissions(self, tikr):
        return [i for i in self.metadata[tikr]['submissions'] if self._is_10q_annotated(tikr, i)]

    """
        Returns whether given tikr submission has annotated ix elements
    """
    def _is_10q_annotated(self, tikr, submission) -> bool:
        
        assert tikr in self.metadata;
        assert submission in self.metadata[tikr]['submissions']

        is_annotated = self.metadata[tikr]['submissions'][submission]['attrs'].get('is_10q_annotated', None)
        if is_annotated is not None:
            return is_annotated
        else:
            return self._gen_10q_annotated_metadata(tikr, submission)
            
    def _gen_10q_annotated_metadata(self, tikr, submission):
                
        annotated_tag_list = {'ix:nonnumeric','ix:nonfraction'}

        _file = None
        files = self.metadata[tikr]['submissions'][submission]['documents']
        for file in files:
            if files[file]['type'] == '10-Q':
                _file = files[file]['filename']
                
        # TODO handle ims-document
        if _file is None:
            warnings.warn("Document Encountered without 10-Q", RuntimeWarning)
            for file in files:
                if files[file].get('is_ims-document', False):
                    self.metadata[tikr]['submissions'][submission]['attrs']['is_10q_annotated'] = False
                    warnings.warn("Encountered unlabeled IMS-DOCUMENT", RuntimeWarning)
                    return False 
            if len(files) == 0:
                warnings.warn("No Files under Document", RuntimeWarning)
                return False

        assert _file is not None, 'Missing 10-Q'

        data = None
        fname = os.path.join(self.data_dir, 'processed', tikr, submission, _file)
        with open(fname, 'r') as f:
            data = f.read();
        for tag in annotated_tag_list:
            if re.search(tag, data):
                self.metadata[tikr]['submissions'][submission]['attrs']['is_10q_annotated'] = True
                return True
        self.metadata[tikr]['submissions'][submission]['attrs']['is_10q_annotated'] = False
        return False


    """
    Parses some documents 2020+ at least

        driver_path -- path of file to open, or 'NONE' to keep current file
        highlight -- add red box around detected fields
        save -- save htm copy (with/without highlighting) to out_path
    """
    def parse_annotated_tables(self, driver_path: str, highlight: bool = False, save: bool = False, out_path: str = os.path.join('.','sample.htm')):
        
        # If path is None, stay on current document
        if driver_path is not None:
            self.driver.get(driver_path)

        found_table = self.driver.find_elements(By.TAG_NAME, 'table')

        table_is_numeric = np.zeros_like(found_table, 'int')# 0: numerical, 1: non-numerical, 2: unannotated
        for i in range(len(found_table)):
            table_is_numeric[i] = 2
            
            # If a table has both non-numeric and non-fraction, the non-fraction takes precedence

            # TODO convert to regex on inner text
            
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

    def get_annotation_info(self, elem: WebElement):
        return {'value': elem.text, 'name': elem.get_attribute('name') , 'id': elem.get_attribute('id')}

    def get_element_info(self, element: WebElement)-> list():
        return {"text": element.text,"location": element.location, "size": element.size}

    def find_page_location(self) -> dict:
        page_breaks = self.driver.find_elements(By.TAG_NAME, 'hr')
        # TODO add logic to handle this
        if len(page_breaks) == 0:
            warnings.warn("No page breaks detected in document", RuntimeWarning)
            return None
        page_number = 1
        # get the range of y for page 1
        page_location = {page_number: [0,page_breaks[0].location["y"]]}
        next_page_start =  page_location[page_number][1] + 2  # plus 2 b/c page break height = 2
        
        # get the range of y for page 2 to  n-1 (n is the last page)
        for hr in page_breaks[1:]:
            page_number += 1
            page_location[page_number]= [next_page_start,hr.location["y"]]
            next_page_start =  page_location[page_number][1] + 2  # plus 2 b/c page break height = 2
        # get the range of y for last page
        page_number += 1
        page_location[page_number]= [next_page_start,float('inf')]
        return page_location

    def get_page_number(self, page_location: dict, element: WebElement) -> int:
        if page_location is None:
            return None, None

        element_y = element.location["y"]
        for i in range(1,len(page_location)+1):
            if( element_y > page_location[i][0] and element_y <page_location[i][1]):
                return i, element_y - page_location[i][0]
            
        return None, None
    #-----------get attribute-------------------------------------------------#
    """
    text - the text value of the annotated label (e.g. 10-Q)
    found_index - index of the parent span webelement in the list of webelements
    full_text - neighboring text (based on the text value of the parent span) (** replace it with new identify neighboring text function)
    anno_index - index of the annotation in the list of annotation based on its webelement
    anno_name - the name attribute from the annotation tag (e.g. us-gaap:SegmentReportingDisclosureTextBlock)
    anno_id - the id attribute from the annotation tag (e.g. id3VybDovL2RvY3MudjEvZG9jOjY0OTlhYTNmZjJk...)
    anno_format - the format attribute from the annotation tag (e.g. ixt:numdotdecimal)
    anno_ix_type - the ix type attribute from the annotation tag (e.g. ix:nonfraction)
    anno_unitref - the unit reference attribute from the annotation tag (e.g. usd)
    anno_decimals - the decimal place attribute from the annotation tag (e.g. -3)
    anno_contextref - the context reference attribute from the annotation tag (e.g. ic6b57dd3d48343d99e743248386420fc_I20201231)
    page_number - the page number for the label
    x - x coordinate
    y - y coordinate base on page number
    height - the height of the tag
    width - the width of the tag
    is_annotated - 1 if the value is annotation, 0 otherwise.
    """
    def get_annotation_features(self, webelements: list, annotations: dict, in_table: np.array, save: bool = False, out_path: str = 'sample.csv'):
        COLUMN_NAMES = ["label_text","found_index","full_text", "anno_index", "anno_name","anno_id",
                        "anno_format","anno_ix_type",'annotation_unitref',"anno_decimals",
                        "anno_contextref","page_number","x","y", "height", "width","is_annotated", "in_table"]
        page_location = self.find_page_location()
        

        
        df = pd.DataFrame(columns=COLUMN_NAMES).astype({"in_table":bool,"is_annotated":bool}) 

        for idx, elem in enumerate(webelements):
            
            default_dict = {attribute: np.nan for attribute in COLUMN_NAMES}
            page_num, y = self.get_page_number(page_location, elem)

            default_dict.update({"found_index": int(idx),"full_text": elem.text, "is_annotated": False,
                                "x": elem.location["x"], "y": y, "page_number": page_num, "name": elem.get_attribute('name'),
                                "height": elem.size["height"], "width": elem.size["width"], "in_table": in_table[idx]})

            count = 0

            new_df = pd.DataFrame(columns=COLUMN_NAMES).astype({"in_table":bool,"is_annotated":bool}) 
            
            for j, annotation in enumerate(annotations[elem]):
                new_dict = default_dict.copy()
                
                val = {"anno_index": j , "x": annotation.location["x"], "is_annotated": True,
                        "label_text": annotation.text, "anno_ix_type": annotation.tag_name}
                
                val["page_number"], val["y"] = self.get_page_number(page_location, annotation)

                for _attr in ["id", "contextref", "decimals", "format", "unitref"]:
                    val[_attr] = annotation.get_attribute(_attr)
                for _size in ["width", "height"]:
                    val[_size] = annotation.size[_size]
                
                new_dict.update(val)
                temp_df = pd.DataFrame(new_dict, index=[0]).astype({"in_table":bool, "is_annotated":bool})
                new_df = pd.concat([temp_df, new_df], ignore_index=True)
                
                count += 1
            

            if count == 0:
                new_df = pd.DataFrame(default_dict, index=[0]).astype({"in_table":bool, "is_annotated":bool})
            df = pd.concat([new_df,df], ignore_index=True)
            """
            default_dict = default_dict if count == 0 else None
            if default_dict != None:
                temp_df = pd.DataFrame(default_dict,index=[0])
                df = pd.concat([temp_df,df], ignore_index=True)
            """

        #df.drop_duplicates(subset = ["text"], keep="last", inplace=True)
        if(save):
            df.to_csv(out_path)
        return df
    
    def featurize_file(self, tikr: str, submission: str, filename: str, force: bool = False):
        """
        
        
        Parameters
        ---------
        tikr: str
            a company identifier to query 
        submission: str
            The filing to access the file from
        filename: str
            The name of the file to featurize
        force: bool, default=False
            if (True), then ignore locally downloaded files and overwrite them. Otherwise, attempt to detect previous download and abort server query.
        """
        if not force and self.metadata.file_was_processed(tikr, submission, filename):
            return self.load_processed(tikr, submission, filename)
        else:
            # TODO make process_file detect and work on unannotated files
            elems, annotation_dict, in_table = self._parse_annotated_text(self.get_driver_path(tikr, submission, filename))
            features = self.get_annotation_features(elems, annotation_dict, in_table)
            self.save_processed(tikr, submission, filename, elems, annotation_dict, features)
            self.metadata.save_tikr_metadata(tikr)
            return features
    
    def save_processed(self, tikr: str, submission: str, filename: str, elems, annotations: dict, features):
        path = os.path.join(self.data_dir, 'parsed', tikr, submission, filename)
        if not os.path.exists(path):
            os.system(f"mkdir -p {path}")
        with open(os.path.join(path, 'features.pkl'), 'wb') as f:
            pkl.dump(features, f)
        self.metadata.file_set_processed(tikr, submission, filename, True)

    def load_processed(self, tikr, submission, filename):
        path = os.path.join(self.data_dir, 'parsed', tikr, submission, filename)
        with open(os.path.join(path, 'features.pkl'), 'rb') as f:
            return pkl.load(f)
        
    def parse_text_by_page(self):
        page_breaks = self.driver.find_elements(By.TAG_NAME, 'hr')
        page_breaks = [ i  for i in page_breaks if i.get_attribute("color") == "#999999" or i.get_attribute("color")== ""]

        
        num_page = len(page_breaks) + 1
        print('total number of page',num_page)
        if(num_page == 1):
            return {}
        text_on_page = {i: {"text": "", "elements": []} for i in range(1,num_page+1)}
        page_number = 1
        hr_parent = page_breaks[0].find_element(By.XPATH, "./..")
        sibling = hr_parent.find_elements(By.XPATH, "./*")

        for elem in sibling:
            ########## highlighting ###################
            if(elem.tag_name == 'hr' and (elem.get_attribute("color") == "#999999" or elem.get_attribute("color") == "")):
                self._draw_border(elem, 'purple')
            elif(page_number % 2 == 0):
                self._draw_border(elem, 'red')
            else:
                self._draw_border(elem, 'blue')
            ########## highlighting ###################

            if(elem.tag_name == 'hr' and (elem.get_attribute("color") == "#999999" or elem.get_attribute("color") == "")):
                page_number += 1
                continue
            text_on_page[page_number]['text'] += "/n" + elem.text
            text_on_page[page_number]["elements"].append(elem)

        self._save_driver_source("sample.html")    
        return text_on_page

    def __del__(self):
        self.driver.quit();
