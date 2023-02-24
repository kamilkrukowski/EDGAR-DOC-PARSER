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
from .document import DocumentType


class Parser:
    """

        Main class for extracting information from HTML documents

    """

    class Element:
        """
            Resembles some behavior of selenium.webelements

            Parameters
            --------------
            info: a set in structure ((tag, attributes),data, range) that
                        contains information of the element. Attributes is
                            in a format of list of set : `[(attr, value)]`

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
            It can also be used on unannotated documents,
                and only the first output is used.

            return
            -------
            root_element: the out most element's tag, attr, and text
            found_annotation: a list of annotated documents
        """

        def __init__(self):
            super(Parser.Span_Parser, self).__init__()
            self.tags_opened = []
            self.found_annotation = []  # ((tag, attr), data)
            self.count = 0  # sanity check, should be len(span_txt)+1
            self.span_txt = ''

        def handle_starttag(self, tag, attrs):
            attrs = tuple(attrs)
            if not self.tags_opened:  # the first tag
                if self.count != 0:
                    raise Exception('multiple root elements')
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
                addition = [(self.tags_opened[-1],
                             data.replace('\n', '').strip() + ' ')]
                self.found_annotation += addition

        # wrap things up into an element, and a list of elements of annotation
        # elements
        def wrapper(self):
            root_element = (self.root_tag, self.span_txt)
            return root_element, self.found_annotation

    def __init__(self, metadata: metadata_manager = None,
                 data_dir: str = 'edgar_data'):
        """
        Parameters
        ---------
        metadata: metadata_manager, default=None
            a meta_manager that can process all metadata
        data_dir: str, default = 'edgar_data'
            string for data directory

        Returns
        --------
        Parser

        Notes
        ------
        Prser extracts information from HTML documents
        """
        self.driver = None

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

    @staticmethod
    def find_all_pattern(pattern, txt):
        """
            helper function that finds element with given tags

            Parameters
            ---------
            pattern -- a list of two strings, corresponding to start
                            and end of an element, ex. '['<span', '</span>']'.
                                The tags to be find and extract
            txt -- the string that containing some html code

            Returns
            --------
            A list of set of two numbers, representing
                the beginning and end position of an element.
        """
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

    @staticmethod
    def labels_in_table(child_span, parent_span):
        """
        check whether strings in child_span is in any of the parent_span
            Parameters
            ---------
            child_span, parent_span: a list of spans

            Returns
            --------
            a list of boolean values
        """

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

    def _parse_unannotated_text(
            self,
            driver_path: str):
        """
        Parses some documents (2001-2013) at least

            driver_path -- path of file to open
            highlight -- add red box around detected fields
            save -- save htm copy (with/without highlighting) to out_path
        """

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

    def get_driver_path(self, tikr, submission, fname, partition):
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
            self, driver_path: str, **kwargs):
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

        found = [i for i in found if i.text not in forbidden]
        annotation_dict2 = dict()
        for i in found:
            annotation_dict2[i] = annotation_dict[i]

        table_range = self.find_all_pattern(self.table_search_key, f)
        in_table = self.labels_in_table([i.range for i in found], table_range)
        return found, annotation_dict, in_table

    def get_unannotated_submissions(self, tikr,
                                    document_type='all',
                                    silent: bool = False) -> list:
        """
            Return list of submissions names without annotations
        """
        document_type = DocumentType(document_type)

        if document_type == 'all':
            return self.get_annotated_submissions(
                tikr=tikr,
                document_type='10q',
                silent=silent) + self.get_annotated_submissions(
                    tikr,
                    document_type='8k', silent=silent)

        submissions = [i for i in self.metadata._get_tikr(tikr)['submissions']]
        out = list()
        for submission in submissions:
            if not self._contains_annotations(
                    tikr=tikr,
                    submission=submission, silent=silent):

                form_type = self.metadata._get_submission(
                    tikr, submission)['attrs']['FORM TYPE']
                form_type = DocumentType(form_type)
                if (form_type == '10-Q' and document_type == '10-Q') or (
                        form_type == '8-K' and document_type == '8-K'):
                    out.append(submission)
                elif form_type == 'other' and document_type == 'other':
                    raise RuntimeWarning(
                        "FORM TYPE \'OTHER\' UNIMPLEMENTED FOR SUBMISSION")

        return out

    def get_annotated_submissions(self, tikr,
                                  document_type='all',
                                  silent: bool = False) -> list:
        """
            Return list of submissions names with annotations
        """
        document_type = DocumentType(document_type)

        if document_type == 'all':
            return self.get_annotated_submissions(
                tikr=tikr,
                document_type='10q',
                silent=silent) + self.get_annotated_submissions(
                    tikr,
                    document_type='8k', silent=silent)

        submissions = [i for i in self.metadata._get_tikr(tikr)['submissions']]
        out = list()
        for submission in submissions:
            if self._contains_annotations(
                    tikr=tikr,
                    submission=submission, silent=silent):

                form_type = self.metadata._get_submission(
                    tikr, submission)['attrs']['FORM TYPE']
                form_type = DocumentType(form_type)
                if (form_type == '10-Q' and document_type == '10-Q') or (
                        form_type == '8-K' and document_type == '8-K'):
                    out.append(submission)
                elif form_type == 'other' and document_type == 'other':
                    raise RuntimeWarning(
                        "FORM TYPE \'OTHER\' UNIMPLEMENTED FOR SUBMISSION")

        return out

    def _contains_annotations(
            self,
            tikr,
            submission,
            silent: bool = False) -> bool:
        """
            Returns whether given tikr submission has annotated ix elements
        """

        assert tikr in self.metadata
        assert submission in self.metadata[tikr]['submissions']

        is_annotated = self.metadata[tikr]['submissions'][submission][
            'attrs'].get('is_annotated', None)
        if is_annotated is not None:
            return is_annotated
        else:
            return self.metadata._gen_submission_metadata(
                tikr, submission, silent=silent)

    """
    Parses some documents 2020+ at least
        driver_path -- path of file to open, or 'NONE' to keep current file
        highlight -- add red box around detected fields
        save -- save htm copy (with/without highlighting) to out_path
    """

    def parse_annotated_tables(
            self,
            driver_path: str,
            save: bool = False):

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
                if found_numeric:
                    table_is_numeric[i] = 0
                continue

            except NoSuchElementException:
                pass

            try:
                found_numeric = found_table[i].find_element(
                    By.TAG_NAME, 'ix:nonnumeric')
                if found_numeric:
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

        return found_table, table_is_numeric

    def get_annotation_info(self, elem: WebElement):
        return {
            'value': elem.text,
            'name': elem.get_attribute('name'),
            'id': elem.get_attribute('id')}

    def get_element_info(self, element: WebElement) -> list():
        return {
            'text': element.text,
            'location': element.location,
            'size': element.size}

    def find_page_location(self) -> dict:
        """


        Parameters
        ---------

        Returns
        --------
        Dictionary
            a dictionary based on page number. The value of the dictionary
                    is the y-coordinates of the corresponding page.


        Notes
        ------

        """
        return None

    def get_page_number(self, page_location: dict, element: WebElement) -> int:
        """


        Parameters
        ---------
        page_location: dict
            a dictionary based on page number. The value is
                the y-coordinates of the corresponding page.
        element: WebElement
            a WebElement to query

        Returns
        --------
        integer
            page number
        integer
            new y-coordinate of the webelement relative
                to the y-coordinate of the page

        Notes
        ------

        """
        if page_location is None:
            return None, None

    # -----------get attribute-----------------------------------------------#
    """
    text - the text value of the annotated label (e.g. 10-Q)
    found_index - index of the parent span webelement
                        in the list of webelements
    full_text - neighboring text (based on the text value of the parent span)
                    (** replace it with new identify neighboring text function)
    anno_index - index of the annotation in the
                    list of annotation based on its webelement
    anno_name - the name attribute from the annotation tag
                    (e.g. us-gaap:SegmentReportingDisclosureTextBlock)
    anno_id - the id attribute from the annotation tag
                    (e.g. id3VybDovL2RvY3MudjEvZG9jOjY0OTlhYTNmZjJk...)
    anno_format - the format attribute from the annotation tag
                        (e.g. ixt:numdotdecimal)
    anno_ix_type - the ix type attribute from the annotation tag
                        (e.g. ix:nonfraction)
    anno_unitref - the unit reference attribute from the annotation tag
                        (e.g. usd)
    anno_decimals - the decimal place attribute from the annotation tag
                        (e.g. -3)
    anno_contextref - the context reference attribute from the annotation tag
                        (e.g. ic6b57dd3d48343d99e743248386420fc_I20201231)
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
            Value is the list of annotation webelement.
                Key is the span webelement.
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
            in the dataframe with a sentinel column ``is_annotated``
                set to False.
        """
        COLUMN_NAMES = [
            'anno_text',
            'found_index',
            'span_text',
            'anno_index',
            'anno_name',
            'anno_id',
            'anno_format',
            'anno_ix_type',
            'anno_unitref',
            'anno_decimals',
            'anno_contextref',
            'page_number',
            'x',
            'y',
            'height',
            'width',
            'is_annotated',
            'in_table']
        df = pd.DataFrame(columns=COLUMN_NAMES)

        for i, elem in enumerate(webelements):

            default_dict = {attribute: None for attribute in COLUMN_NAMES}
            page_num, y = None, None

            default_dict.update({'anno_text': None,
                                 'found_index': int(i),
                                 'span_text': elem.text,
                                 'is_annotated': 0,
                                 'x': elem.location['x'],
                                 'y': y,
                                 'page_number': page_num,
                                 'height': elem.size['height'],
                                 'width': elem.size['width'],
                                 'in_table': int(in_table[i])})

            count = 0

            new_df = pd.DataFrame(columns=COLUMN_NAMES)
            for j, annotation in enumerate(annotations[elem]):
                new_dict = default_dict.copy()

                val = {
                    'anno_index': j,
                    'x': annotation.location['x'],
                    'is_annotated': 1,
                    'anno_text': annotation.text,
                    'anno_ix_type': annotation.tag_name}

                val['page_number'], val['y'] = None, None

                for _attr in ['name', 'id', 'contextref']:
                    val[f'anno_{_attr}'] = annotation.get_attribute(_attr)
                for _size in ['width', 'height']:
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

        df = df.astype({'in_table': bool, 'is_annotated': bool})
        df.drop_duplicates(
            subset=['anno_text', 'anno_id'], keep='last', inplace=True)

        if (save):
            df.to_csv(out_path)
        return df

    def featurize_file(
            self,
            tikr: str,
            submission: str,
            filename: str,
            force: bool = False,
            silent: bool = False,
            remove_raw: bool = False,
            **kwargs):
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
        remove_raw: bool
                default to be False. If true, the raw data will be deleted
                    after parsing and caching result.

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
        out = None
        document_type = self.metadata.get_doctype(tikr, submission, filename)
        f_anno_file = pathlib.Path(
            os.path.join(
                self.data_dir,
                DocumentType.EXTRACTED_FILE_DIR_NAME,
                tikr,
                f'{document_type}',
                submission,
                filename)).absolute()

        # Try to load from cache
        if not force and self.metadata.file_was_processed(
                tikr, submission, filename):
            out = self.load_processed(tikr, submission,
                                      filename, document_type=document_type)
        # Regenerate data
        else:
            if document_type != '10-Q' and document_type != '8-K':
                raise NotImplementedError(
                    f'Not implemented for current form type {document_type}')

            # TODO make process_file detect and work on unannotated files
            if not self._contains_annotations(tikr, submission, silent=silent):
                raise NotImplementedError('Not annotated')
            if not (os.path.exists(f_anno_file)):
                warnings.warn('File not loaded locally', RuntimeWarning)
                return
            elems, annotation_dict, in_table = self._parse_annotated_text(
                f_anno_file)
            features = self.get_annotation_features(
                elems, annotation_dict, in_table)
            self.save_processed(tikr, submission, filename,
                                document_type, features)
            self.metadata.save_tikr_metadata(tikr)
            out = features

        if remove_raw:
            # Try remove the file
            if os.path.exists(f_anno_file):
                os.remove(f_anno_file)

            # Try remove documentType/submission/file
            parent_dir = pathlib.Path(
                os.path.normpath(
                    os.path.join(f_anno_file, os.pardir))).absolute()
            if os.path.exists(parent_dir) and len(
                    os.listdir(parent_dir)) == 0:
                os.rmdir(parent_dir)

            # Try remove documentType/submission/file
            parent_dir = pathlib.Path(
                os.path.normpath(
                    os.path.join(parent_dir, os.pardir))).absolute()
            if os.path.exists(parent_dir) and len(
                    os.listdir(parent_dir)) == 0:
                os.rmdir(parent_dir)

            # Try remove tikr/documentType/submission/file
            parent_dir = pathlib.Path(
                os.path.normpath(
                    os.path.join(parent_dir, os.pardir))).absolute()
            if os.path.exists(parent_dir) and len(
                    os.listdir(parent_dir)) == 0:
                os.rmdir(parent_dir)

            # Try remove DocumentType.EXTRACTION_DIR/tikr/
            #   documentType/submission/file

            parent_dir = pathlib.Path(
                os.path.normpath(
                    os.path.join(parent_dir, os.pardir))).absolute()
            if os.path.exists(parent_dir) and len(
                    os.listdir(parent_dir)) == 0:
                os.rmdir(parent_dir)
        return out

    def save_processed(
            self,
            tikr: str,
            submission: str,
            filename: str,
            document_type,
            features):
        path = os.path.join(self.data_dir, DocumentType.PARSED_FILE_DIR_NAME,
                            tikr, f'{submission}',
                            f'{document_type}', filename)
        if not os.path.exists(path):
            os.system(f'mkdir -p {path}')
        with open(os.path.join(path, 'features.pkl'), 'wb') as f:
            pkl.dump(features, f)
        self.metadata.file_set_processed(tikr, submission, filename, True)

    def load_processed(self, tikr, submission, filename, document_type):
        path = os.path.join(self.data_dir, DocumentType.PARSED_FILE_DIR_NAME,
                            tikr, submission, f'{document_type}', filename)
        with open(os.path.join(path, 'features.pkl'), 'rb') as f:
            return pkl.load(f)

    def __del__(self):
        if self.driver is not None:
            self._get_driver().quit()
