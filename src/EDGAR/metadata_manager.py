import os
import pathlib
import pickle as pkl
from yaml import load, CLoader as Loader, dump, CDumper as Dumper
import warnings
import urllib.request
import json

from .document import DocumentType


class metadata_manager(dict):
    def __init__(self, data_dir='data', *arg, **kw):
        super(metadata_manager, self).__init__(*arg, **kw)

        # Always gets the path of the current file
        self.data_dir = data_dir

        self.meta_dir = os.path.join(
            self.data_dir, DocumentType.META_FILE_DIR_NAME)
        if not os.path.exists(self.meta_dir):
            os.system('mkdir -p ' + self.meta_dir)

        # Used by dataloader for API
        self.keys_path = os.path.join(self.data_dir, '.keys.yaml')
        self.keys = None

    def reset(self):
        for file in os.listdir(self.meta_dir):
            os.remove(os.path.join(self.meta_dir, file))
        # Keep API Keys
        self.save_keys()
        self.clear()

    def load_keys(self):

        if not os.path.exists(self.keys_path):
            warnings.warn("No .keys.yaml located", RuntimeWarning)
            self.keys = dict()
            return
        self.keys = load(open(self.keys_path, 'r'), Loader=Loader)

    def save_keys(self):

        dump(self.keys, open(self.keys_path, 'w'), Dumper=Dumper)

    def load_tikr_metadata(self, tikr):

        data_path = os.path.join(self.meta_dir, f"{tikr}.pkl")
        if os.path.exists(data_path):

            with open(data_path, 'rb') as f:
                self[tikr] = pkl.load(f)
            return True

        self.initialize_tikr_metadata(tikr)

        return False

    def save_tikr_metadata(self, tikr):

        self.initialize_tikr_metadata(tikr)

        data_path = os.path.join(self.meta_dir, f"{tikr}.pkl")

        with open(data_path, 'wb') as f:
            pkl.dump(self.get(tikr), f)

    def _get_tikr(self, tikr):
        if tikr not in self:
            self.load_tikr_metadata(tikr)
        return self[tikr]

    def initialize_tikr_metadata(self, tikr):
        if tikr not in self:
            self[tikr] = {'attrs': dict(), 'submissions': dict()}

    def initialize_submission_metadata(self, tikr, fname):
        pdict = self[tikr]['submissions']
        if fname not in pdict:
            pdict[fname] = {'attrs': dict(), 'documents': dict()}

    def get_doctype(self, tikr, submission, filename):
        sequence = self.find_sequence_of_file(
            tikr=tikr, submission=submission, filename=filename)
        form_type = self._get_submission(tikr, submission)['documents']
        form_type = form_type[sequence]['type']

        if DocumentType.is_valid_type(form_type):
            form_type = DocumentType(form_type)
        else:
            form_type = DocumentType('other')

        return form_type

    def get_10q_name(self, tikr, submission):
        """
        Parameters
        ---------
        tikr: str
            a company identifier to query
        submission:
            the associated company filing for which to find a 10-Q form


        Returns
        --------
        filename: str
            The name of the 10-q file associated with the submission, or None
        """
        files = self._get_submission(tikr, submission)['documents']
        for file in files:
            if files[file]['type'] in ['10-Q', 'FORM 10-Q']:
                return files[file]['filename']
        return None

    def get_8k_name(self, tikr, submission):
        """
        Parameters
        ---------
        tikr: str
            a company identifier to query
        submission:
            the associated company filing for which to find a 10-Q form


        Returns
        --------
        filename: str
            The name of the 8-k file associated with the submission, or None
        """
        files = self._get_submission(tikr, submission)['documents']
        for file in files:
            if files[file]['type'] in ['8-K', 'FORM 8-K', '8K']:
                return files[file]['filename']
        return None

    def _get_submission(self, tikr, submission):
        tikr_data = self._get_tikr(tikr)['submissions']
        if submission not in tikr_data:
            raise NameError(
                f"{submission} for {tikr} not found in {self.data_dir}")
        return tikr_data[submission]

    def get_submissions(self, tikr):
        """
        Parameters
        ---------
        tikr: str
            a company identifier to query

        Returns
        --------
        submissions: list
            a list of string names of filing submissions under the company tikr

        """
        if 'submissions' in self[tikr]:
            return [i for i in self[tikr]['submissions']]
        return None

    def find_sequence_of_file(self, tikr: str, submission: str, filename: str):
        level = self[tikr]['submissions'][submission]['documents']
        for sequence in level:
            if level[sequence]['filename'] == filename:
                return sequence
        return None

    def file_set_processed(
            self,
            tikr: str,
            submission: str,
            filename: str,
            val: bool):
        sequence = self.find_sequence_of_file(tikr, submission, filename)
        assert sequence is not None, "Error: filename not found"
        self._get_submission(tikr, submission)['documents'][sequence][
            'features_pregenerated'] = val

    def file_was_processed(self, tikr: str, submission: str, filename: str):
        sequence = self.find_sequence_of_file(tikr, submission, filename)
        assert sequence is not None, "Error: filename not found"
        doc = self[tikr]['submissions'][submission]['documents'][sequence]
        return doc.get('features_pregenerated', False)

    def set_downloaded(self, tikr: str, value: bool = True):
        self._get_tikr(tikr)['attrs']['downloaded'] = value
        self.save_tikr_metadata(tikr)

    def is_downloaded(self, tikr):
        """
            Returns True if TIKR had previous bulk download
        """
        return self._get_tikr(tikr)['attrs'].get('downloaded', False)

    def set_unpacked(self, tikr, document_type, value=True):

        document_type = DocumentType(document_type)
        self._get_tikr(tikr)['attrs'][f'unpacked_{document_type}'] = value
        self.save_tikr_metadata(tikr)

    def is_unpacked(self, tikr, document_type):
        """
            Returns True if TIKR had previous bulk download
        """
        document_type = DocumentType(document_type)
        return self._get_tikr(tikr)['attrs'].get(
            f'unpacked_{document_type}', False)

    def get_tikr_list(self):
        """
        Download tikr list if not exist to the data folder.
            Parse into list of tickers

        Returns
        --------
        tikr : list
            a list of string tickers

        """
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        tikr_fpath = os.path.join(self.data_dir, "company_tickers.json")
        if not os.path.isfile(tikr_fpath):
            urllib.request.urlretrieve(
                "https://www.sec.gov/files/company_tickers.json", tikr_fpath)
        with open(tikr_fpath) as json_file:
            data = json.load(json_file)
        return [data[i]['ticker'] for i in data]

    def offload_submission_file(self, tikr, submission):

        document_type = self._get_submission(
            tikr, submission)['attrs']['FORM TYPE']
        spath = pathlib.Path(
            os.path.join(
                self.data_dir,
                DocumentType.EXTRACTED_FILE_DIR_NAME,
                tikr,
                f'{document_type}',
                submission)).absolute()
        if os.path.exists(spath):
            for file in os.listdir(spath):
                os.remove(os.path.join(spath, file))
            os.rmdir(spath)

        self._get_tikr(tikr)['submissions'].pop(submission)
        self.save_tikr_metadata(tikr)

        # Check delete parents
        doctype_dir = pathlib.Path(os.path.normpath(
            os.path.join(spath, os.pardir))).absolute()
        if os.path.exists(doctype_dir) and len(os.listdir(doctype_dir)) == 0:
            os.rmdir(doctype_dir)
            tikr_dir = pathlib.Path(os.path.normpath(
                os.path.join(doctype_dir, os.pardir))).absolute()
            if os.path.exists(tikr_dir) and len(os.listdir(tikr_dir)) == 0:
                os.rmdir(tikr_dir)
                extraction_dir = pathlib.Path(os.path.normpath(
                    os.path.join(tikr_dir, os.pardir))).absolute()
                if os.path.exists(extraction_dir) and len(
                        os.listdir(extraction_dir)) == 0:
                    os.rmdir(extraction_dir)
