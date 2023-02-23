from secedgar import filings, FilingType
from bs4 import BeautifulSoup

import os
import warnings
import datetime
import sys
from tqdm.auto import tqdm
from time import sleep

from .document import DocumentType


class Downloader:
    """Class for querying SEC-EDGAR database for files."""

    def __init__(self, data_dir: str = 'edgar_data', metadata=None):
        """Initialize Downloader."""
        # our HTML files are so big and nested that the standard
        #   1000 limit is too small.
        sys.setrecursionlimit(10000000)

        # Always gets the path of the current file
        self.data_dir = data_dir
        # Download and processed directories
        self.raw_dir = os.path.join(
            self.data_dir, DocumentType.RAW_FILE_DIR_NAME)
        self.proc_dir = os.path.join(
            self.data_dir, DocumentType.PARSED_FILE_DIR_NAME)

        self.metadata = metadata

        # Loads keys
        self.metadata.load_keys()

        # Generate new API Header if missing
        if 'edgar_email' not in self.metadata.keys or (
                'edgar_agent' not in self.metadata.keys):
            print(
                ('No API Header detected.\n'
                 'The SEC requires all EDGAR API users '
                 'to identify themselves\n\n'))
            if 'edgar_agent' not in self.metadata.keys:
                print(
                    ('The SEC requires a legal name of '
                     'the user and any organizational affiliation'))
                answer = 'n'
                while (answer[0] != 'y' or len(answer) > 4):
                    self.metadata.keys['edgar_agent'] = input('User(s): ')
                    answer = input(
                        ('Input User(s) '
                         f"\'{self.metadata.keys['edgar_agent']}\'\n"
                         ' Is this correct? (y/n)'))
            if 'edgar_email' not in self.metadata.keys:
                print('The SEC requires a contact email for the API user')
                answer = 'n'
                while (answer[0] != 'y' or len(answer) > 4):
                    self.metadata.keys['edgar_email'] = input('Email: ')
                    answer = input(
                        ('Input Email '
                         f"\'{self.metadata.keys['edgar_email']}\'\n"
                         ' Is this correct? (y/n)'))
            self.metadata.save_keys()

    def _gen_tikr_metadata(self, tikr: str, documents, key):
        """Generate the metadata for a given tikr."""
        out = dict()

        for doc in documents:

            seq = doc.find('sequence')
            i = 20
            while ('\n') not in seq.text[:i]:
                i += 20

            seq = seq.text[:i].split('\n')[0]
            out[seq] = dict()

            for nextElem in ['type', 'filename', 'description']:
                doc2 = doc.find(nextElem)

                # Sentinel for missing fields in early 2000s
                if doc2 is None:
                    if nextElem == 'filename':
                        out[seq][nextElem] = f'{seq}.htm'
                    else:
                        out[seq][nextElem] = ''
                    continue

                i = 20
                while ('\n') not in doc2.text[:i]:
                    i += 20
                out[seq][nextElem] = doc2.text[:i].split('\n')[0]

            out[seq]['extracted'] = False

        # Extend existing tikr metadata with new results,
        #   or start with empty dict and add new results
        self.metadata.initialize_tikr_metadata(tikr)

        # Extending documents in existing submission or start new one
        self.metadata.initialize_submission_metadata(tikr, key)

        # Add documents to submission of tikr
        self.metadata[tikr]['submissions'][key]['documents'] = \
            dict(out, **self.metadata[tikr]['submissions'][key]['documents'])

    def query_server(
            self, tikr: str, delay_time: int = 1,
            force: bool = False, **kwargs):
        """
        Download SEC filings to a local directory for parsing by TIKR.

        Parameters
        ---------
        tikr: str
            a company identifier to query
        force: bool
            if (True), then ignore locally downloaded files
                and overwrite them. Otherwise, attempt to detect
                    previous download and abort server query.
        start_date: optional
            The earliest date to look for filings
        end_date: optional
            The latest filing date retrievable
        max_num_filings:
            The maximum number of documents to retrieve. Retrieves all
                documents if set to `None`.
        delay_time:
            The time (in seconds) delayed at the
                beginning of this function.
        """
        sleep(delay_time)

        if self.metadata.is_downloaded(tikr) and not force:
            print('\talready downloaded')
            return

        elif (kwargs.get('start_date', None) is None and (
                kwargs.get('end_date', None) is None) and (
              kwargs.get('max_num_filings', None) is None)
              ):

            self.metadata.set_downloaded(tikr, True)

        user_agent = ''.join([f"{self.metadata.keys['edgar_agent']}",
                              f": {self.metadata.keys['edgar_email']}"])
        document_type = kwargs.get('document_type', '10-Q').replace(
            '-', '').lower()
        assert document_type in {'10q', '8k', None}

        if document_type == '10q':
            filing_type = FilingType.FILING_10Q
        elif document_type == '8k':
            filing_type = FilingType.FILING_8K
        else:
            filing_type = None
        f = filings(cik_lookup=tikr,
                    filing_type=filing_type,
                    count=kwargs.get('max_num_filings', None),
                    user_agent=user_agent,
                    start_date=kwargs.get('start_date', None),
                    end_date=kwargs.get('end_date', None))

        # Beautiful Soup parsing XML as HTML error
        #   (Ignored because we are using iXML HTML markup)
        warnings.simplefilter('ignore')
        f.save(self.raw_dir)
        warnings.simplefilter('default')

    def get_unpackable_files(
            self, tikr: str, document_type: str = 'all', **kwargs):
        """
        Get list of targets for unpack_file func.

        Parameters
        ---------
        tikr: str
            a company identifier to query
        document_type: str
            document type to unpack (10-Q, 8-K, or all)
        """
        # sec-edgar data save location for documents filing ticker
        document_type = DocumentType(document_type)

        if document_type == 'all':
            return self.get_unpackable_files(
                tikr=tikr, document_type='10q',
                **kwargs) + self.get_unpackable_files(
                tikr=tikr, document_type='8k', **kwargs)

        d_dir = os.path.join(self.raw_dir, f'{tikr}', f'{document_type}')
        if not os.path.exists(d_dir):
            return []
        return os.listdir(d_dir)

    def get_submissions(self, tikr, **kwargs):
        """
        Get list of submissions under tikr.

        Parameters
        ---------
        tikr: str
            a company identifier to query
        document_type: str
            document type to unpack (10-Q, 8-K, or all)
        """
        # sec-edgar data save location for filing ticker
        return [i.split('.txt')[0] for i in self.get_unpackable_files(
            tikr, document_type=kwargs.get('document_type', '10q'))]

    valid_unpack_types = {
        'FORM 10-Q', '10-Q', 'FORM 8-K', '8-K'}

    def __unpack_doc__(
            self, tikr, submission, doc, document_type, force=True):
        """
        Private utility, parses SEC submission dump into components.

        Parameters
        ----------
        tikr: str
            the company the document belongs to
        submission: str
            the submission the document is from
        doc: str
        """
        submission = submission.split('.')[0]

        metadata = self.metadata._get_submission(tikr, submission)['documents']

        seq = doc.find('sequence')
        i = 20
        while ('\n') not in seq.text[:i]:
            i += 20
        sequence = seq.text[:i].split('\n')[0]

        # Do not repeat work unless forcing
        if metadata[sequence]['extracted'] and not force:
            return

        form_type = metadata[sequence]['type']
        if document_type != 'all':
            if not DocumentType.is_valid_type(form_type):
                return
            form_type = DocumentType(form_type)
        else:
            if DocumentType.is_valid_type(form_type):
                form_type = DocumentType(form_type)
            else:
                form_type = 'other'

        filename = metadata[sequence]['filename']

        ensure_path = os.path.join(
            self.data_dir, DocumentType.EXTRACTED_FILE_DIR_NAME)
        if not os.path.exists(ensure_path):
            os.mkdir(ensure_path)
        ensure_path = os.path.join(ensure_path, f'{tikr}')
        if not os.path.exists(ensure_path):
            os.mkdir(ensure_path)
        ensure_path = os.path.join(ensure_path, f'{document_type}')
        if not os.path.exists(ensure_path):
            os.mkdir(ensure_path)
        ensure_path = os.path.join(ensure_path, submission)
        if not os.path.exists(ensure_path):
            os.mkdir(ensure_path)

        out_path = None
        if form_type == '10q':
            if document_type == 'all' or document_type == '10q':
                out_path = os.path.join(
                    self.data_dir, DocumentType.EXTRACTED_FILE_DIR_NAME,
                    f'{tikr}', f'{document_type}')
        elif form_type == '8k':
            if document_type == 'all' or document_type == '8k':
                out_path = os.path.join(self.data_dir,
                                        DocumentType.EXTRACTED_FILE_DIR_NAME,
                                        f'{tikr}', f'{document_type}')

        with open(
                os.path.join(out_path, submission, filename),
                'w', encoding='utf-8') as f:

            f.write(doc.prettify())
            metadata[sequence]['extracted'] = True

    def unpack_file(self, tikr, file, document_type='all',
                    force=True, remove_raw=False, **kwargs):
        """
        Process raw data from one filing at one company.

            See utility function for getting file names.

        Parameters
        ---------
        tikr: str
            company ticker associated with unpacking
        filename: str
            filing submission to unpack
        complete: bool
            If False, only unpacks 10-Q, otherwise all documents.
        document_type: str
            document type to unpack (10-Q, 8-K, or all)
        force: bool
            if (True), then ignore locally downloaded files and
                overwrite them. Otherwise, attempt to detect
                previous download and abort server query.
        clean_raw: bool
            default to be true. If true, the raw data will be
                cleaned after parsed.
        """
        # sec-edgar data save location for documents filing ticker
        document_type = DocumentType(document_type)

        d_dir = os.path.join(self.raw_dir, f'{tikr}', f'{document_type}')
        content = None
        with open(os.path.join(d_dir, file), 'r', encoding='utf-8') as f:
            content = f.read().strip()

        d = BeautifulSoup(content, features='lxml').body

        fname = file.split('.txt')[0]
        p = d.find('sec-document')
        if p is None:
            p = d.find('ims-document')
            if p is not None:
                warnings.warn(
                    'IMS-DOCUMENT skipped during loading', RuntimeWarning)
                if fname not in self.metadata['submissions']:
                    self.metadata.initialize_submission_metadata(tikr, fname)
                self.metadata._get_submission(tikr, fname)['attrs'][
                    'is_ims-document'] = True
                return
        d = p
        assert d is not None, 'No sec-document tag found in submission'

        documents = d.find_all('document', recursive=False)

        self._gen_tikr_metadata(tikr, documents, fname)

        sec_header = d.find('sec-header').text.replace('\t', '').split('\n')
        sec_header = [i for i in sec_header if ':' in i]
        attrs = {i.split(':')[0]: i.split(':')[1] for i in sec_header}
        self.metadata._get_tikr(tikr)['submissions'][fname]['attrs'] = attrs

        for doc in documents:
            self.__unpack_doc__(
                tikr, fname, doc, document_type=document_type, force=force)

        if remove_raw:
            os.remove(os.path.join(d_dir, file))
            self.metadata.set_downloaded(tikr, False)

        self.metadata.save_tikr_metadata(tikr)

    def _is_10q_unpacked(self, tikr):
        """Check if 10-Q has been unpacked."""
        return self.metadata[tikr]['attrs'].get('10q_extracted', False)

    def _is_8k_unpacked(self, tikr):
        """Check if 8-K has been unpacked."""
        return self.metadata[tikr]['attrs'].get('8k_extracted', False)

    # TODO: Is this function used/necessary?
    def _is_fully_unpacked(self, tikr):
        """Check if all documents have been unpacked."""
        return self.metadata[tikr]['attrs'].get('complete_extracted', False)

    def unpack_bulk(
            self, tikr, force=False, loading_bar=False,
            desc='Inflating HTM', remove_raw=False,
            document_type='all', silent=False):
        """
        Process all raw data from one company.

        Parameters
        ---------
        tikr: str
            company ticker associated with unpacking
        force: bool
            if (True), then ignore locally downloaded files and
                overwrite them. Otherwise, attempt to detect
                previous download and abort server query.
        loading__bar: bool:
            if True, will time and show progress
        document_type: str
            document type to unpack (10-Q, 8-K, or all)

        """
        document_type = DocumentType(document_type)
        if document_type == 'all':
            self.unpack_bulk(tikr, force=force, loading_bar=False,
                             desc=desc, remove_raw=remove_raw,
                             document_type='10q', silent=silent)
            self.unpack_bulk(tikr, force=force, loading_bar=False,
                             desc=desc, remove_raw=remove_raw,
                             document_type='8k', silent=silent)
            return

        # Early quitting conditions
        if not force:
            if document_type == '10q' and self._is_10q_unpacked(tikr):
                return
            if document_type == '8k' and self._is_8k_unpacked(tikr):
                return

        # Read each text submission dump for each quarterly filing
        files = self.get_unpackable_files(
            tikr, document_type=document_type)

        itera = files
        if loading_bar:
            itera = tqdm(itera, desc=desc, leave=False)

        for file in itera:
            self.unpack_file(
                tikr,
                file,
                document_type=document_type,
                force=force,
                silent=silent,
                remove_raw=remove_raw)

        # TODO if we unpack 10-q then 8-k we should have all unpacked
        self.metadata.set_unpacked(
            tikr, document_type=document_type, value=True)

        # Delete raw files if desired
        d_dir = os.path.join(self.raw_dir, f'{tikr}', f'{document_type}')
        if remove_raw and os.path.exists(d_dir):
            os.rmdir(d_dir)
            # If all filings have now been removed, clean up tikr directory
            parent_dir = os.path.join(self.raw_dir, f'{tikr}')
            if len(os.listdir(parent_dir)) == 0:
                os.rmdir(parent_dir)
                if len(os.listdir(self.raw_dir)) == 0:
                    os.rmdir(self.raw_dir)

        self.metadata.save_tikr_metadata(tikr)

    def get_dates(self, tikr, **kwargs):
        """Return the filing submission txt closest to provided date."""
        out = dict()
        for i in self.get_submissions(
            tikr, document_type=kwargs.get(
                'document_type', 'all')):
            date_str = self.metadata[tikr]['submissions'][i]['attrs'].get(
                'FILED AS OF DATE', None)
            if date_str is None:
                print('broken')
            out[datetime.datetime.strptime(date_str, '%Y%m%d')] = i
        return out

    def get_nearest_date_filename(
            self, tikr, date, return_date=False, prefer_recent=True, **kwargs):
        """
        Get the nearest date of the filename.

        Parameters
        ---------
        tikr: str
            a company identifier to query
        date: str
            date in format  AAAABBCC format (Year, Month, Day) with 0 padding
        return_date: bool

        prefer_recent: bool

        document_type: str
            document type to unpack (10-Q, 8-K, or all)
        """
        # Provide AAAABBCC format (Year, Month, Day) with 0 padding
        if isinstance(date, str):
            assert len(date) == 8, 'String format wrong'
            date = datetime.datetime.strptime(date, '%Y%m%d')
        assert isinstance(date, datetime.datetime), 'Wrong format'

        dates = self.get_dates(
            tikr, document_type=kwargs.get('document_type', 'all'))
        keys = sorted(list(dates.keys()))

        if date in dates:
            return date

        for (start, stop) in zip(keys[:-1], keys[1:]):
            if start < date and date < stop:
                if prefer_recent:
                    if return_date:
                        return dates[stop].split('.txt')[0], stop
                    return dates[stop].split('.txt')[0]
                else:
                    if return_date:
                        return dates[start].split('.txt')[0], start
                    return dates[start].split('.txt')[0]

    def __del__(self):
        """Set recursion limit."""
        # back to normal
        sys.setrecursionlimit(1000)
