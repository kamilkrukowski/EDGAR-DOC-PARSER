"""The Metadata class tracks the attributes of files as they are parsed."""

import os
import re
import pathlib
import pickle as pkl
from yaml import load, CLoader as Loader, dump, CDumper as Dumper
import warnings
import urllib.request
import json

from .document import DocumentType


class metadata_manager(dict):
    """Track the application of EDGAR functions, and hold the metadata\
    attributes of files as they are accessed."""

    def __init__(self, data_dir, *arg, **kw):
        """
        Create Metadata Object.

        Parameters
        ---------
        data_dir: str
            The location where EDGAR data is stored
        """
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

    def reset(self, keep_api_header: bool = True):
        """
        Delete stored metadata about investigated companies.

        Parameters
        ---------
        keep_api_header: Bool, default True
            If True, then does not delete api-header information.
        """
        for file in os.listdir(self.meta_dir):
            os.remove(os.path.join(self.meta_dir, file))
        # Keep API Keys
        if keep_api_header:
            self.save_keys()
        self.clear()

    def load_keys(self):
        """Load APIKEYs from local directory."""
        if not os.path.exists(self.keys_path):
            warnings.warn('No .keys.yaml located', RuntimeWarning)
            self.keys = dict()
            return
        self.keys = load(open(self.keys_path, 'r'), Loader=Loader)

    def save_keys(self):
        """Save current APIKEYs to local directory."""
        dump(self.keys, open(self.keys_path, 'w'), Dumper=Dumper)

    def load_tikr_metadata(self, tikr):
        """Load previously generated metadata and add to current."""
        data_path = os.path.join(self.meta_dir, f'{tikr}.pkl')
        if os.path.exists(data_path):

            with open(data_path, 'rb') as f:
                self[tikr] = pkl.load(f)
            return True

        self.initialize_tikr_metadata(tikr)

        return False

    def save_tikr_metadata(self, tikr):
        """Offload metadata to file, for later loading."""
        self.initialize_tikr_metadata(tikr)

        data_path = os.path.join(self.meta_dir, f'{tikr}.pkl')

        with open(data_path, 'wb') as f:
            pkl.dump(self.get(tikr), f)

    def _get_tikr(self, tikr):
        """Safe get function for company entries in metadata."""
        if tikr not in self:
            self.load_tikr_metadata(tikr)
        return self[tikr]

    def initialize_tikr_metadata(self, tikr):
        """Generate a company entry in metadata if not yet present."""
        if tikr not in self:
            self[tikr] = {'attrs': dict(), 'submissions': dict()}

    def initialize_submission_metadata(self, tikr, submission):
        """Generate a submission entry for a company tikr if not present."""
        pdict = self[tikr]['submissions']
        if submission not in pdict:
            pdict[submission] = {'attrs': dict(), 'documents': dict()}

    def get_doctype(self, tikr, submission, filename):
        """
        Return the document type of a file.

        Notes
        -----
        While a 10-Q filing has a 10-Q file associated, a 10-Q filing may have
        several supplementary materials included of different document types.
        """
        sequence = self.find_sequence_of_file(
            tikr=tikr, submission=submission, filename=filename)
        form_type = self._get_submission(tikr, submission)['documents']
        form_type = form_type[sequence]['type']

        if DocumentType.is_valid_type(form_type):
            form_type = DocumentType(form_type)
        else:
            form_type = DocumentType('other')

        return form_type

    def get_primary_doc_name(self, tikr: str, submission: str,
                             document_type: str = None):
        """
        Get the name of the primary document in a submission.

        Parameters
        ----------
        tikr: str
            a company identifier to query
        submission: str
            The associated company filing to find the primary form for.

        TODO not implemented
        """
        raise NotImplementedError()

    def get_10q_name(self, tikr, submission):
        """
        Get the primary document name of an 10-Q filing.

        Parameters
        ---------
        tikr: str
            a company identifier to query
        submission:
            the associated company filing for which to find a 10-Q form


        Returns
        --------
        filename: str, None
            The name of the submission's 10-Q file, or None
        """
        files = self._get_submission(tikr, submission)['documents']
        for file in files:
            if files[file]['type'] in ['10-Q', 'FORM 10-Q']:
                return files[file]['filename']
        return None

    def get_8k_name(self, tikr, submission):
        """
        Get the primary document name of an 8-K filing.

        Parameters
        ---------
        tikr: str
            a company identifier to query
        submission:
            the associated company filing for which to find a 8-K form

        Returns
        --------
        filename: str, None
            The name of the submission's 8-K file, or None
        """
        files = self._get_submission(tikr, submission)['documents']
        for file in files:
            if files[file]['type'] in ['8-K', 'FORM 8-K', '8K']:
                return files[file]['filename']
        return None

    def _get_submission(self, tikr: str, submission: str) -> dict:
        """Safe get function for submission under a company."""
        tikr_data = self._get_tikr(tikr)['submissions']
        if submission not in tikr_data:
            raise NameError(
                f'{submission} for {tikr} not found in {self.data_dir}')
        return tikr_data[submission]

    def get_submissions(self, tikr):
        """
        Get a list of filing submissions under a company.

        Parameters
        ---------
        tikr: str
            a company identifier to query
        """
        return list(self._get_tikr(tikr)['submissions'].keys())

    def find_sequence_of_file(self, tikr: str, submission: str, filename: str):
        """
        Return the Official SEC numerical indexing for a submitted file.

        Notes
        -----
        Each submission has an associated collection of documents that are
        identified by their sequence.

        Sequence counts upwards from 1, but may skip numbers. It is typical
        but not guaranteed that the primary file has sequence 1 and the
        supplementary materials ascend in sequence.
        """
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
        """Set the status for file_was_processed function."""
        sequence = self.find_sequence_of_file(tikr, submission, filename)
        assert sequence is not None, 'Error: filename not found'
        self._get_submission(tikr, submission)['documents'][sequence][
            'features_pregenerated'] = val
        self.save_tikr_metadata(tikr)

    def file_was_processed(self, tikr: str, submission: str, filename: str):
        """
        Return True if file has a loaded copy available locally.

        Notes
        -----
        This indicates whether there is any extra information available
        for download from the SEC EDGAR database, but does not track
        new releases.
        """
        sequence = self.find_sequence_of_file(tikr, submission, filename)
        assert sequence is not None, 'Error: filename not found'
        doc = self[tikr]['submissions'][submission]['documents'][sequence]
        return doc.get('features_pregenerated', False)

    def set_downloaded(self, tikr: str, value: bool = True):
        """Set the status for is_downloaded function."""
        self._get_tikr(tikr)['attrs']['downloaded'] = value
        self.save_tikr_metadata(tikr)

    def is_downloaded(self, tikr: str):
        """
        Return True if TIKR has local results of bulk download.

        Notes
        -----
        This indicates whether there is any extra information available
        for download from the SEC EDGAR database, but does not track
        new releases.
        """
        return self._get_tikr(tikr)['attrs'].get('downloaded', False)

    def set_unpacked(self, tikr, document_type, value=True):
        """Set the status for is_unpacked function."""
        document_type = DocumentType(document_type)
        self._get_tikr(tikr)['attrs'][f'unpacked_{document_type}'] = value
        self.save_tikr_metadata(tikr)

    def is_unpacked(self, tikr: str, document_type: str):
        """
        Return True if TIKR had previously unpacked all instances of \
        this document type, and they are present locally.

        Parameters
        ------------
        document_type: str or DocumentType
            The document type in question
        """
        document_type = DocumentType(document_type)
        return self._get_tikr(tikr)['attrs'].get(
            f'unpacked_{document_type}', False)

    def get_tikr_list(self):
        """
        Download list of all companies in the SEC database if not already \
        present. Return list of valid company ticker targets for download.

        Returns
        --------
        tikr : list[str]
            All SEC filing company public stock tickers.
        """
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        tikr_fpath = os.path.join(self.data_dir, 'company_tickers.json')
        if not os.path.isfile(tikr_fpath):
            urllib.request.urlretrieve(
                'https://www.sec.gov/files/company_tickers.json', tikr_fpath)
        with open(tikr_fpath) as json_file:
            data = json.load(json_file)
        return [data[i]['ticker'] for i in data]

    def offload_submission_file(self, tikr: str, submission: str):
        """Delete submission from local dataset, removing it from disk."""
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

    def _gen_submission_metadata(
            self, tikr, submission, silent: bool = False, **kwargs):
        """
        Generate attrs for a filing submission.

        Parameters
        ----------
        tikr: str
            Represent Company to query submission
        submission: str
            The filing to generate metadata attrs for
        silent: bool
            if True, does not display warnings
        """
        annotated_tag_list = {'ix:nonnumeric', 'ix:nonfraction'}

        _file = None
        files = self._get_submission(tikr, submission)['documents']
        for file in files:
            # We hope these are mutually exclusive
            if files[file]['type'] == '10-Q' or files[file]['type'] == '8-K':
                _file = files[file]['filename']

        # TODO handle ims-document
        if _file is None:
            if silent:
                return False
            else:
                warnings.warn(
                    'Document Encountered without 10-Q or 8-K', RuntimeWarning)
                for file in files:
                    if files[file].get('is_ims-document', False):
                        self.metadata[tikr]['submissions'][submission][
                            'attrs']['is_annotated'] = False
                        warnings.warn(
                            'Encountered unlabeled IMS-DOCUMENT',
                            RuntimeWarning)
                        return False
                if len(files) == 0:
                    warnings.warn('No Files under Document', RuntimeWarning)
                    return False

        assert _file is not None, 'Missing 10-Q or 8-K'

        document_type = kwargs.get('document_type', None)
        if document_type is None:
            document_type = self._get_submission(
                tikr, submission)['attrs']['FORM TYPE']
            document_type = DocumentType(document_type)

        data = None
        fname = os.path.join(self.data_dir,
                             DocumentType.EXTRACTED_FILE_DIR_NAME,
                             tikr, f'{document_type}', submission)
        files = os.listdir(fname)

        for file in files:
            with open(os.path.join(fname, file), 'r', encoding='utf-8') as f:
                data = f.read()
            for tag in annotated_tag_list:
                if re.search(tag, data):
                    self._get_submission(tikr, submission)['attrs'][
                        'is_annotated'] = True
                    return True
        self._get_submission(tikr, submission)['attrs'][
            'is_annotated'] = False
        return False
