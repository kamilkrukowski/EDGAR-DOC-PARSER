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
from html.parser import HTMLParser

from .metadata_manager import metadata_manager


class edgar_parser:
    """

        Main class for extracting information from HTML documents

    """

    class Element:
        """
            Resembles some behavior of selenium.webelements

            Parameters
            --------------
<<<<<<< HEAD
<<<<<<< HEAD
            info: a set in structure ((tag, attributes),data, range) that contains information of the element.
                        Attributes is in a format of list of set : `[(attr, value)]`
=======
            info: a set in structure ((tag, attributes),data, range) that contains information of the element. Attributes is in a format of list of set : `[(attr, value)]`
>>>>>>> 01fa547 (autopep8 aggressive src)
=======
            info: a set in structure ((tag, attributes),data, range) that contains information of the element.
                        Attributes is in a format of list of set : `[(attr, value)]`
>>>>>>> c6bbdd9 (Aggressive autopep8)

            attributes
            ----------
            text
            tag_name

            method
            ------
            get_attribute(attr): attr as a string
        """

        def __init__(self, info):
            self.text = info[1].strip()
            self.tag_name = info[0][0]
            self.range = info[2]
            self.attributes = dict()
            self.size = {'width': 0, 'height': 0}
            self.location = {'x': 0, 'y': 0}
            for attr_pair in info[0][1]:
                self.attributes[attr_pair[0]] = attr_pair[1]

        def get_attribute(self, attr):
            if attr in self.attributes:
                return self.attributes[attr]
            else:
                return None

    class Span_Parser(HTMLParser):
        """
            Class that handles the a string of span element
            It can also be used on unannotated documents, and only the first output is used.

            return
            -------
            root_element: the out most element's tag, attr, and text
            found_annotation: a list of annotated documents
        """

        def __init__(self):
            super(edgar_parser.Span_Parser, self).__init__()
            self.tags_opened = []
            self.found_annotation = []  # ((tag, attr), data)
            self.count = 0  # sanity check, should be len(span_txt)+1
            self.span_txt = ''

        def handle_starttag(self, tag, attrs):
            attrs = tuple(attrs)
            if not self.tags_opened:  # the first tag
                if self.count != 0:
                    raise Exception("multiple root elements")
                self.root_tag = (tag, attrs)
            self.tags_opened += [(tag, attrs)]

        def handle_endtag(self, tag):
            self.tags_opened = self.tags_opened[:-1]
            if not self.tags_opened:  # no more tags opened.
                self.count += 1

        def handle_data(self, data):
            self.span_txt += data.replace('\n', '').strip() + ' '
            if len(self.tags_opened) == 1:  # the out most tag
                self.count += 1
            if self.tags_opened[-1][0] in annot_tag:  # in annotation element
                self.found_annotation += [(self.tags_opened[-1],
                                           data.replace('\n', '').strip() + ' ')]

        # wrap things up into an element, and a list of elements of annotation
        # elements
        def wrapper(self):
            root_element = (self.root_tag, self.span_txt)
            return root_element, self.found_annotation

    def __init__(self, metadata: metadata_manager,
                 data_dir: str,
                 headless: bool = True):
        """


        Parameters
        ---------
        metadata: metadata_manager, default=None
            a meta_manager that can process all metadata
        data_dir: str, default = 'edgar_download'
            string for data directory
         headless: bool, default=True
            If (True), it will launch browser without UI

        Returns
        --------
        edgar_parser

        Notes
        ------
        edgar_parser extracts information from HTML documents
        """
        self.driver = None
        self.headless = headless

        self.data_dir = data_dir

        if metadata is None:
            self.metadata = metadata_manager(data_dir=self.data_dir)
        else:
            self.metadata = metadata

        self._annotation_preparation()

    # generate search keys from tag name

    def _annotation_preparation(self):
        # the list of known tags
        global annot_tag
        annot_tag = ['ix:nonnumeric', 'ix:nonfraction']
        global unannot_tag
        unannot_tag = ['font']

        annot_search_pattern = []
        unannot_search_pattern = []
        for tag in annot_tag:
            key = [0, 1]
            key[0] = '<' + tag
            key[1] = '</' + tag + '>'
            annot_search_pattern += [key]
        for tag in unannot_tag:
            key[0] = '<' + tag
            key[1] = '</' + tag + '>'
            unannot_search_pattern += [key]
        self.span_search_key = ['<span', '</span>']
        self.table_search_key = ['<table', '</table>']
        self.annot_search_pattern = annot_search_pattern
        self.unannot_search_pattern = unannot_search_pattern

    """
        helper function that finds element with given tags

        Parameters
        ---------
        pattern -- a list of two strings, corresponding to start and end of an element,
                        ex. '['<span', '</span>']'. The tags to be find and extract
        txt -- the string taht containing some html code

        Returns
        --------
        A list of set of two numbers, representing the begining and end positon of an element.
    """
    @staticmethod
    def find_all_pattern(pattern, txt):
        starts = list(re.finditer(pattern[0], txt))
        ends = list(re.finditer(pattern[1], txt))
        tag_finds = sorted(starts + ends, key=lambda x: x.span()[0])

        result = []
        unmatched_start = []
        for mo in tag_finds:
            if mo.group()[1] != '/':  # begin
                unmatched_start += [mo]
            else:
                result += [(unmatched_start[-1], mo)]
                unmatched_start = unmatched_start[:-1]

        result1 = [(i[0].span()[0], i[1].span()[1]) for i in result]
        return result1

    """
    check whether strings in child_span is in any of the parent_span
        Parameters
        ---------
        child_span, parent_span: a list of spans

        Returns
        --------
        a list of boolean values
    """
    @staticmethod
    def labels_in_table(child_span, parent_span):

        # print('child_span:', child_span)

        child_in_parent = np.zeros(len(child_span))
        l_p = 0
        t_p = 0
        label_len = len(child_span)
        table_len = len(parent_span)
        while l_p < label_len and t_p < table_len:
            # check if it is in a table
            if child_span[l_p][0] < parent_span[t_p][0]:  # not in table yet
                l_p += 1
            elif child_span[l_p][0] < parent_span[t_p][1]:  # in tabel
                child_in_parent[l_p] = 1
                l_p += 1
            else:
                t_p += 1
        return child_in_parent

    """
    Parses some documents (2001-2013) at least

        driver_path -- path of file to open
        highlight -- add red box around detected fields
        save -- save htm copy (with/without highlighting) to out_path
    """

    def _parse_unannotated_text(
        self,
        driver_path: str,
        highlight: bool = False,
        save: bool = False,
        out_path: str = os.path.join(
            '.',
            'sample.htm')):

        with open(driver_path, encoding='utf-8') as file:
            f = file.read()
        found_range = []
        found_range += self.find_all_pattern(self.unannot_search_pattern[0], f)
        found = []
        for pair in found_range:
            elem_parser = self.Span_Parser()
            elem_parser.feed(f[pair[0]:pair[1]])
            root, waste = elem_parser.wrapper()
            found += [self.Element(root + (pair,))]
        # Filter symbols using 'hashmap' set
        forbidden = {
            i for i in "\'\" (){}[],./\\-+^*`'`;:<>%#@$"}.union({'', '**'})
        found = [i for i in found if i.text not in forbidden]

        return found

    """
        Get a driver filename uri path from data identifiers
    """

    def get_driver_path(self, tikr, submission, fname, partition='processed'):
        # return pathlib.Path(os.path.join(self.data_dir, partition, tikr,
        # submission, fname)).absolute().as_uri()
        return pathlib.Path(
            os.path.join(
                self.data_dir,
                partition,
                tikr,
                submission,
                fname)).absolute()

    def _parse_annotated_text(
        self,
        driver_path: str,
        highlight: bool = False,
        save: bool = False,
        out_path: str = os.path.join(
            '.',
            'sample.htm')):
        """
        Parses some documents 2020+ at least

            driver_path -- path of file to open as a file path format
            highlight -- add red box around detected fields
            save -- save htm copy (with/without highlighting) to out_path
        """

        with open(driver_path, encoding='utf-8') as file:
            f = file.read()
        found_range = []
        found_range += self.find_all_pattern(self.span_search_key, f)
        found = []
        annotation_dict = dict()
        for pair in found_range:
            elem_parser = self.Span_Parser()
            elem_parser.feed(f[pair[0]:pair[1]])
            root, annotation_found = elem_parser.wrapper()
            root_element = self.Element(root + (pair,))
            found += [root_element]
            annotation_element_found = [self.Element(
                i + ('',)) for i in annotation_found]
            annotation_dict[root_element] = annotation_element_found
        forbidden = {
            i for i in "\'\" (){}[],./\\-+^*`'`;:<>%#@$"}.union({'', '**'})

        # print('f: \n', len(f))
        # print('found before forbidden: ', found)

        found = [i for i in found if i.text not in forbidden]
        annotation_dict2 = dict()
        for i in found:
            annotation_dict2[i] = annotation_dict[i]

        # print('found: ', found)

        table_range = self.find_all_pattern(self.table_search_key, f)
        in_table = self.labels_in_table([i.range for i in found], table_range)
        return found, annotation_dict, in_table

    """
        Return list of submissions names with annotated 10-Q forms
    """

    def get_annotated_submissions(self, tikr, silent: bool = False):
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        return [i for i in self.metadata[tikr]['submissions'] if self._is_10q_annotated(tikr, i, silent=silent) or self._is_8k_annotated(tikr, i, silent=silent)]
=======
        return [i for i in self.metadata[tikr]['submissions']
                if self._is_10q_annotated(tikr, i, silent=silent)]
>>>>>>> 01fa547 (autopep8 aggressive src)
=======
        return [i for i in self.metadata[tikr]['submissions']
                if self._is_10q_annotated(tikr, i, silent=silent)]
=======
        return [i for i in self.metadata[tikr]['submissions'] if self._is_10q_annotated(tikr, i, silent=silent) or self._is_8k_annotated(tikr, i, silent=silent)]
>>>>>>> 9ac5426 (download and parse 8-k and 10-q or all)
>>>>>>> 4ba9685 (download and parse 8-k and 10-q or all)
=======
        return [i for i in self.metadata[tikr]['submissions']
                if self._is_10q_annotated(tikr, i, silent=silent)]
>>>>>>> 01fa547 (autopep8 aggressive src)
=======
        return [i for i in self.metadata[tikr]['submissions']
                if self._is_10q_annotated(tikr, i, silent=silent)]
=======
        return [i for i in self.metadata[tikr]['submissions'] if self._is_10q_annotated(tikr, i, silent=silent) or self._is_8k_annotated(tikr, i, silent=silent)]
>>>>>>> 9ac5426 (download and parse 8-k and 10-q or all)
>>>>>>> 9b40315 (download and parse 8-k and 10-q or all)

    """
        Returns whether given tikr submission has annotated ix elements
    """
<<<<<<< HEAD

    def _is_10q_annotated(
            self,
            tikr,
            submission,
            silent: bool = False) -> bool:

        assert tikr in self.metadata
        assert submission in self.metadata[tikr]['submissions']

        is_annotated = self.metadata[tikr]['submissions'][submission][
            'attrs'].get('is_10q_annotated', None)
        if is_annotated is not None:
            return is_annotated
        else:
            return self._gen_10q_annotated_metadata(
                tikr, submission, silent=silent)

<<<<<<< HEAD
<<<<<<< HEAD
    def _is_8k_annotated(self, tikr, submission, silent: bool = False) -> bool:
=======
>>>>>>> 01fa547 (autopep8 aggressive src)

    def _is_10q_annotated(
            self,
            tikr,
            submission,
            silent: bool = False) -> bool:

        assert tikr in self.metadata
        assert submission in self.metadata[tikr]['submissions']

<<<<<<< HEAD
<<<<<<< HEAD
        is_annotated = self.metadata[tikr]['submissions'][submission]['attrs'].get('is_8k_annotated', None)
        if is_annotated is not None:
            return is_annotated
        else:
            return self._gen_8k_annotated_metadata(tikr, submission, silent=silent)

    def _gen_10q_annotated_metadata(self, tikr, submission, silent: bool = False):
=======
    def _gen_10q_annotated_metadata(
            self, tikr, submission, silent: bool = False):
>>>>>>> 01fa547 (autopep8 aggressive src)
=======
    def _gen_10q_annotated_metadata(
            self, tikr, submission, silent: bool = False):
=======
    def _is_8k_annotated(self, tikr, submission, silent: bool = False) -> bool:

        assert tikr in self.metadata;
        assert submission in self.metadata[tikr]['submissions']

        is_annotated = self.metadata[tikr]['submissions'][submission]['attrs'].get('is_8k_annotated', None)
        if is_annotated is not None:
            return is_annotated
        else:
            return self._gen_8k_annotated_metadata(tikr, submission, silent=silent)

    def _gen_10q_annotated_metadata(self, tikr, submission, silent: bool = False):
>>>>>>> 9ac5426 (download and parse 8-k and 10-q or all)
>>>>>>> 4ba9685 (download and parse 8-k and 10-q or all)

=======
        is_annotated = self.metadata[tikr]['submissions'][submission]['attrs'].get(
            'is_10q_annotated', None)
=======
        is_annotated = self.metadata[tikr]['submissions'][submission][
            'attrs'].get('is_10q_annotated', None)
>>>>>>> c6bbdd9 (Aggressive autopep8)
        if is_annotated is not None:
            return is_annotated
        else:
            return self._gen_10q_annotated_metadata(
                tikr, submission, silent=silent)

<<<<<<< HEAD
    def _gen_10q_annotated_metadata(
            self, tikr, submission, silent: bool = False):
=======
    def _is_8k_annotated(self, tikr, submission, silent: bool = False) -> bool:

        assert tikr in self.metadata;
        assert submission in self.metadata[tikr]['submissions']

        is_annotated = self.metadata[tikr]['submissions'][submission]['attrs'].get('is_8k_annotated', None)
        if is_annotated is not None:
            return is_annotated
        else:
            return self._gen_8k_annotated_metadata(tikr, submission, silent=silent)

    def _gen_10q_annotated_metadata(self, tikr, submission, silent: bool = False):
>>>>>>> 9ac5426 (download and parse 8-k and 10-q or all)

>>>>>>> 01fa547 (autopep8 aggressive src)
        annotated_tag_list = {'ix:nonnumeric', 'ix:nonfraction'}

        _file = None
        files = self.metadata[tikr]['submissions'][submission]['documents']
        for file in files:
            if files[file]['type'] == '10-Q':
                _file = files[file]['filename']

        # TODO handle ims-document
        if _file is None:
            if silent:
                return False
<<<<<<< HEAD
            else:
                warnings.warn(
                    "Document Encountered without 10-Q", RuntimeWarning)
                for file in files:
                    if files[file].get('is_ims-document', False):
                        self.metadata[tikr]['submissions'][submission][
                            'attrs']['is_10q_annotated'] = False
                        warnings.warn(
                            "Encountered unlabeled IMS-DOCUMENT",
                            RuntimeWarning)
                        return False
                if len(files) == 0:
                    warnings.warn("No Files under Document", RuntimeWarning)
                    return False

        assert _file is not None, 'Missing 10-Q'

        data = None
        fname = os.path.join(self.data_dir, 'processed',
                             tikr, submission, _file)
        with open(fname, 'r', encoding = 'utf-8') as f:
<<<<<<< HEAD
            data = f.read()
        for tag in annotated_tag_list:
            if re.search(tag, data):
                self.metadata[tikr]['submissions'][submission]['attrs'][
                    'is_10q_annotated'] = True
                return True
        self.metadata[tikr]['submissions'][submission]['attrs'][
            'is_10q_annotated'] = False
        return False

<<<<<<< HEAD
<<<<<<< HEAD
=======
=======
>>>>>>> 4ba9685 (download and parse 8-k and 10-q or all)
    def _gen_8k_annotated_metadata(self, tikr, submission, silent: bool = False):

        annotated_tag_list = {'ix:nonnumeric','ix:nonfraction'}

        _file = None
        files = self.metadata[tikr]['submissions'][submission]['documents']
        for file in files:
            if files[file]['type'] == '8-K':
                _file = files[file]['filename']

        # TODO handle ims-document
        if _file is None:
            if silent:
                return False;
            else:
                warnings.warn("Document Encountered without 8-K", RuntimeWarning)
                for file in files:
                    if files[file].get('is_ims-document', False):
                        self.metadata[tikr]['submissions'][submission]['attrs']['is_8k_annotated'] = False
                        warnings.warn("Encountered unlabeled IMS-DOCUMENT", RuntimeWarning)
=======
            else:
                warnings.warn(
                    "Document Encountered without 10-Q", RuntimeWarning)
                for file in files:
                    if files[file].get('is_ims-document', False):
                        self.metadata[tikr]['submissions'][submission]['attrs']['is_10q_annotated'] = False
                        warnings.warn(
                            "Encountered unlabeled IMS-DOCUMENT",
                            RuntimeWarning)
>>>>>>> 01fa547 (autopep8 aggressive src)
                        return False
                if len(files) == 0:
                    warnings.warn("No Files under Document", RuntimeWarning)
                    return False

        assert _file is not None, 'Missing 8-K'

        data = None
        fname = os.path.join(self.data_dir, 'processed',
                             tikr, submission, _file)
        with open(fname, 'r') as f:
=======
>>>>>>> 76fe6ed (clean raw data)
            data = f.read()
        for tag in annotated_tag_list:
            if re.search(tag, data):
<<<<<<< HEAD
                self.metadata[tikr]['submissions'][submission]['attrs']['is_8k_annotated'] = True
                return True
        self.metadata[tikr]['submissions'][submission]['attrs']['is_8k_annotated'] = False
=======
                self.metadata[tikr]['submissions'][submission]['attrs'][
                    'is_10q_annotated'] = True
                return True
        self.metadata[tikr]['submissions'][submission]['attrs'][
            'is_10q_annotated'] = False
>>>>>>> c6bbdd9 (Aggressive autopep8)
        return False

<<<<<<< HEAD
<<<<<<< HEAD

<<<<<<< HEAD
=======
>>>>>>> 01fa547 (autopep8 aggressive src)
=======
>>>>>>> 9ac5426 (download and parse 8-k and 10-q or all)
>>>>>>> 4ba9685 (download and parse 8-k and 10-q or all)
=======
>>>>>>> 01fa547 (autopep8 aggressive src)
=======
=======
    def _gen_8k_annotated_metadata(self, tikr, submission, silent: bool = False):

        annotated_tag_list = {'ix:nonnumeric','ix:nonfraction'}

        _file = None
        files = self.metadata[tikr]['submissions'][submission]['documents']
        for file in files:
            if files[file]['type'] == '8-K':
                _file = files[file]['filename']

        # TODO handle ims-document
        if _file is None:
            if silent:
                return False;
            else:
                warnings.warn("Document Encountered without 8-K", RuntimeWarning)
                for file in files:
                    if files[file].get('is_ims-document', False):
                        self.metadata[tikr]['submissions'][submission]['attrs']['is_8k_annotated'] = False
                        warnings.warn("Encountered unlabeled IMS-DOCUMENT", RuntimeWarning)
                        return False
                if len(files) == 0:
                    warnings.warn("No Files under Document", RuntimeWarning)
                    return False

        assert _file is not None, 'Missing 8-K'

        data = None
        fname = os.path.join(self.data_dir, 'processed', tikr, submission, _file)
        with open(fname, 'r') as f:
            data = f.read();
        for tag in annotated_tag_list:
            if re.search(tag, data):
                self.metadata[tikr]['submissions'][submission]['attrs']['is_8k_annotated'] = True
                return True
        self.metadata[tikr]['submissions'][submission]['attrs']['is_8k_annotated'] = False
        return False


>>>>>>> 9ac5426 (download and parse 8-k and 10-q or all)
>>>>>>> 9b40315 (download and parse 8-k and 10-q or all)
    """
    Parses some documents 2020+ at least

        driver_path -- path of file to open, or 'NONE' to keep current file
        highlight -- add red box around detected fields
        save -- save htm copy (with/without highlighting) to out_path
    """

    def parse_annotated_tables(
        self,
        driver_path: str,
        highlight: bool = False,
        save: bool = False,
        out_path: str = os.path.join(
            '.',
            'sample.htm')):

        # If path is None, stay on current document
        if driver_path is not None:
            self._get_driver().get(driver_path)

        found_table = self._get_driver().find_elements(By.TAG_NAME, 'table')

        # 0: numerical, 1: non-numerical, 2: unannotated
        table_is_numeric = np.zeros_like(found_table, 'int')
        for i in range(len(found_table)):
            table_is_numeric[i] = 2

            # If a table has both non-numeric and non-fraction, the
            # non-fraction takes precedence

            # TODO convert to regex on inner text

            try:
                found_numeric = found_table[i].find_element(
                    By.TAG_NAME, 'ix:nonfraction')
                table_is_numeric[i] = 0
                continue

            except NoSuchElementException:
                pass

            try:
                found_numeric = found_table[i].find_element(
                    By.TAG_NAME, 'ix:nonnumeric')
                table_is_numeric[i] = 1

            except NoSuchElementException:
                pass

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
        return {
            'value': elem.text,
            'name': elem.get_attribute('name'),
            'id': elem.get_attribute('id')}

    def get_element_info(self, element: WebElement) -> list():
        return {
            "text": element.text,
            "location": element.location,
            "size": element.size}

    def find_page_location(self) -> dict:
        """


        Parameters
        ---------

        Returns
        --------
        Dictionary
            a dictionary based on page number. The value of the dictionary is the y-coordinates of the corresponding page.


        Notes
        ------

        """
#         page_breaks = self._get_driver().find_elements(By.TAG_NAME, 'hr')
#         page_breaks = [ i  for i in page_breaks if i.get_attribute("color") == "#999999" or i.get_attribute("color")== ""]
#         # TODO add logic to handle this
#         if len(page_breaks) == 0:
#             warnings.warn("No page breaks detected in document", RuntimeWarning)
#             return None
#         page_number = 1
#         # get the range of y for page 1
#         page_location = {page_number: [0,page_breaks[0].location["y"]]}
#         next_page_start =  page_location[page_number][1]

#         # get the range of y for page 2 to  n-1 (n is the last page)
#         for hr in page_breaks[1:]:
#             page_number += 1
#             page_location[page_number]= [next_page_start,hr.location["y"]]
#             next_page_start =  page_location[page_number][1]
#         # get the range of y for last page
#         page_number += 1
#         page_location[page_number]= [next_page_start,float('inf')]
#         return page_location
        return None

    def get_page_number(self, page_location: dict, element: WebElement) -> int:
        """


        Parameters
        ---------
        page_location: dict
            a dictionary based on page number. The value is the y-coordinates of the corresponding page.
        element: WebElement
            a WebElement to query

        Returns
        --------
        integer
            page number
        integer
            new y-coordinate of the webelement relative to the y-coordinate of the page

        Notes
        ------

        """
        if page_location is None:
            return None, None

    # -----------get attribute-------------------------------------------------#
    """
    text - the text value of the annotated label (e.g. 10-Q)
    found_index - index of the parent span webelement in the list of webelements
    full_text - neighboring text (based on the text value of the parent span)
                    (** replace it with new identify neighboring text function)
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

    def get_annotation_features(
            self,
            webelements: list,
            annotations: dict,
            in_table: np.array,
            save: bool = False,
            out_path: str = 'sample.csv'):
        """


        Parameters
        ---------
        webelements: list[WebElement]
            list of span WebElement
        annotations: dict
            Value is the list of annotation webelement. Key is the span webelement.
        in_table: list[Boolean]
            list of boolean. If (True), then it is table related webelement.
        save: bool, default=False
            if (True), then store the Dataframe into a CSV file.
        out_path: str, default='sample.csv'
            if save is True, then store the output into CSV file at out_path.

        Returns
        --------
        DataFrame
            Each row corresponds to one text field. Rows are not unique,
                one is generated for each iXBRL annotation on that text field.


        Notes
        ------
        Documents without annotations receive entries
            in the dataframe with a sentinel column ``is_annotated`` set to False.
        """
        COLUMN_NAMES = [
            "anno_text",
            "found_index",
            "span_text",
            "anno_index",
            "anno_name",
            "anno_id",
            "anno_format",
            "anno_ix_type",
            'anno_unitref',
            "anno_decimals",
            "anno_contextref",
            "page_number",
            "x",
            "y",
            "height",
            "width",
            "is_annotated",
            "in_table"]
        page_location = None  # page number and y range
        df = pd.DataFrame(columns=COLUMN_NAMES)

        for i, elem in enumerate(webelements):

            default_dict = {attribute: None for attribute in COLUMN_NAMES}
            page_num, y = None, None

            default_dict.update({"anno_text": None,
                                 "found_index": int(i),
                                 "span_text": elem.text,
                                 "is_annotated": 0,
                                 "x": elem.location["x"],
                                 "y": y,
                                 "page_number": page_num,
                                 "height": elem.size["height"],
                                 "width": elem.size["width"],
                                 "in_table": int(in_table[i])})

            count = 0

            new_df = pd.DataFrame(columns=COLUMN_NAMES)
            for j, annotation in enumerate(annotations[elem]):
                new_dict = default_dict.copy()

                val = {
                    "anno_index": j,
                    "x": annotation.location["x"],
                    "is_annotated": 1,
                    "anno_text": annotation.text,
                    "anno_ix_type": annotation.tag_name}

                val["page_number"], val["y"] = None, None

                for _attr in ["name", "id", "contextref"]:
                    val[f"anno_{_attr}"] = annotation.get_attribute(_attr)
                for _size in ["width", "height"]:
                    val[_size] = annotation.size[_size]

                new_dict.update(val)
                temp_df = pd.DataFrame(new_dict, index=[0])
                new_df = pd.concat([temp_df, new_df], ignore_index=True)

                count += 1

            if count == 0:
                new_df = pd.DataFrame(default_dict, index=[0])
            df = pd.concat([new_df, df], ignore_index=True)
            """
            default_dict = default_dict if count == 0 else None
            if default_dict != None:
                temp_df = pd.DataFrame(default_dict,index=[0])
                df = pd.concat([temp_df,df], ignore_index=True)
            """

        df = df.astype({"in_table": bool, "is_annotated": bool})
        df.drop_duplicates(
            subset=["anno_text", "anno_id"], keep="last", inplace=True)

        if (save):
            df.to_csv(out_path)
        return df

    def featurize_file(
            self,
            tikr: str,
            submission: str,
            filename: str,
            force: bool = False,
<<<<<<< HEAD
<<<<<<< HEAD
            silent: bool = False,
            **kwargs):
=======
            silent: bool = False):
>>>>>>> 01fa547 (autopep8 aggressive src)
=======
            silent: bool = False,
            **kwargs):
>>>>>>> 76fe6ed (clean raw data)
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
            if (True), then ignore locally downloaded files and
                overwrite them. Otherwise, attempt to detect previous download
                    and abort server query.
        silent: bool default=False
            if (True), then does not print runtime warnings.
        clean_raw: bool
                default to be False. If true, the raw data will be cleaned after parsed. 

        Returns
        --------
        DataFrame
            Each row corresponds to one text field. Rows are not unique,
             one is generated for each iXBRL annotation on that text field.


        Notes
        ------
        Documents without annotations receive entries in the dataframe
            The sentinel column ``is_annotated`` set to False.
        """
        if not force and self.metadata.file_was_processed(
                tikr, submission, filename):
            return self.load_processed(tikr, submission, filename)
        else:
            # TODO make process_file detect and work on unannotated files
            if not self._is_10q_annotated(tikr, submission, silent=silent) and not self._is_8k_annotated(tikr, submission, silent=silent) :
                raise NotImplementedError
            elems, annotation_dict, in_table = self._parse_annotated_text(
                self.get_driver_path(tikr, submission, filename))
            features = self.get_annotation_features(
                elems, annotation_dict, in_table)
            self.save_processed(tikr, submission, filename,
                                elems, annotation_dict, features)
            self.metadata.save_tikr_metadata(tikr)
            if kwargs.get('clean_raw', False):
                os.remove(self.get_driver_path(tikr, submission, filename))
            return features

    def save_processed(
            self,
            tikr: str,
            submission: str,
            filename: str,
            elems,
            annotations: dict,
            features):
        path = os.path.join(self.data_dir, 'parsed',
                            tikr, submission, filename)
        if not os.path.exists(path):
            os.system(f"mkdir -p {path}")
        with open(os.path.join(path, 'features.pkl'), 'wb') as f:
            pkl.dump(features, f)
        self.metadata.file_set_processed(tikr, submission, filename, True)

    def load_processed(self, tikr, submission, filename):
        path = os.path.join(self.data_dir, 'parsed',
                            tikr, submission, filename)
        with open(os.path.join(path, 'features.pkl'), 'rb') as f:
            return pkl.load(f)

    def __del__(self):
        if self.driver is not None:
            self._get_driver().quit()
