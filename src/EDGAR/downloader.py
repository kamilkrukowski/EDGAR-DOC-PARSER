"""Module for querying SEC-EDGAR database remotely and saving locally."""
from secedgar import filings, FilingType
from secedgar.exceptions import NoFilingsError
from bs4 import BeautifulSoup

import os
import warnings
import datetime
import sys
import contextlib
from time import sleep
from tqdm.auto import tqdm

from .document import DocumentType
from .metadata_manager import metadata_manager


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

        if metadata is None:
            self.metadata = metadata_manager(data_dir=self.data_dir)
        else:
            self.metadata = metadata

        # Loads keys
        self.metadata.load_keys()

        # Generate new API Header if missing
        if 'edgar_email' not in self.metadata.keys or (
                'edgar_agent' not in self.metadata.keys):
            self.generate_api_header()

    def generate_api_header(self):
        """Generate API key from commandline user input prompts."""
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
                if i > 600:
                    print(f"\'{seq.text[:i]}\'")
                    print(doc.text[:100])
                    raise RuntimeError

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

                skip = False
                i = 20
                while ('\n') not in doc2.text[:i]:
                    i += 20
                    if i > 600:
                        skip = True
                        # type: GRAPHIC elements have no <description>
                        # after <filename>
                        if nextElem != 'description' and out[seq][
                                'type'] != 'GRAPHIC':
                            raise RuntimeError
                        break

                if not skip:
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
            self, tikr: str, document_type: str = 'all', delay_time: int = 1,
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
        document_type = DocumentType(document_type)

        filing_type = None
        if document_type.dtype == '10-Q':
            filing_type = FilingType.FILING_10Q
        elif document_type.dtype == '8-K':
            filing_type = FilingType.FILING_8K
        else:
            raise NotImplementedError('Query does not support this doctype')

        f = filings(cik_lookup=tikr,
                    filing_type=filing_type,
                    count=kwargs.get('max_num_filings', None),
                    user_agent=user_agent,
                    start_date=kwargs.get('start_date', None),
                    end_date=kwargs.get('end_date', None))

        # Beautiful Soup parsing XML as HTML error
        #   (Ignored because we are using iXML HTML markup)
        warnings.simplefilter('ignore')
        # We redirect an unavoidable loading bar
        with contextlib.redirect_stderr(open(os.devnull, 'w')):
            with contextlib.redirect_stdout(open(os.devnull, 'w')):
                try:
                    f.save(self.raw_dir)
                except NoFilingsError:
                    self.metadata.set_downloaded(tikr, True)
                    self.metadata.set_unpacked(
                        tikr, document_type=document_type, value=True)
                    warnings.warn(f'No Filings Under {tikr}', RuntimeWarning)
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
                tikr=tikr, document_type='10-Q',
                **kwargs) + self.get_unpackable_files(
                tikr=tikr, document_type='8-K', **kwargs)

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
            tikr, document_type=kwargs.get('document_type', '10-Q'))]

    valid_unpack_types = {
        'FORM 10-Q', '10-Q', 'FORM 8-K', '8-K'}

    def __unpack_doc__(
            self, tikr, submission, doc, document_type, force=True,
            include_supplementary: bool = False):
        """
        Private utility, parses SEC submission dump into components.

        Parameters
        ----------
        tikr: str
            the company the document belongs to
        submission: str
            the submission the document is from
        doc: str
            the html document being parsed

        Returns
        -------
        success: bool
            If the document is properly supported and succesfully extracted.
        """
        submission = submission.split('.')[0]
        metadata = self.metadata._get_submission(tikr, submission)['documents']

        seq = doc.find('sequence')
        i = 20
        while ('\n') not in seq.text[:i]:
            i += 20
        sequence = seq.text[:i].split('\n')[0]

        # Do not repeat work unless forcing
        if metadata[sequence].get('extracted', False) and not force:
            return

        form_type = metadata[sequence]['type']
        if document_type == 'all' or include_supplementary:
            if DocumentType.is_valid_type(form_type):
                form_type = DocumentType(form_type)
            else:
                form_type = 'other'
        else:
            if not DocumentType.is_valid_type(form_type):
                return
            form_type = DocumentType(form_type)

        filename = metadata[sequence]['filename']

        if '.htm' not in filename:
            if '.jpg' in filename or '.png' in filename:
                warnings.warn('Images not yet supported', RuntimeWarning)
            elif '.txt' in filename:
                warnings.warn('Pure .TXT not yet supported', RuntimeWarning)
            else:
                warnings.warn("Non HTML documents are not yet supported",
                              RuntimeWarning)
            return False

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
        if form_type == '10-Q':
            if document_type == 'all' or document_type == '10-Q':
                out_path = os.path.join(
                    self.data_dir, DocumentType.EXTRACTED_FILE_DIR_NAME,
                    f'{tikr}', f'{document_type}')
        elif form_type == '8-K':
            if document_type == 'all' or document_type == '8-K':
                out_path = os.path.join(self.data_dir,
                                        DocumentType.EXTRACTED_FILE_DIR_NAME,
                                        f'{tikr}', f'{document_type}')
        elif form_type == 'other':
            out_path = os.path.join(self.data_dir,
                                    DocumentType.EXTRACTED_FILE_DIR_NAME,
                                    f'{tikr}', f'{document_type}')
        else:
            raise NotImplementedError

        with open(
                os.path.join(out_path, submission, filename),
                'w', encoding='utf-8') as f:

            f.write(doc.prettify())
            metadata[sequence]['extracted'] = True

        return True

    def unpack_file(self, tikr, file, document_type='all',
                    force=True, remove_raw=False,
                    include_supplementary: bool = False, **kwargs):
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
        remove_raw: bool = False
            If (True), the raw data will be deleted after parsing.
        include_supplementary: bool = False
            If (True), unpacks all supplementary documents to the main one.
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
                if fname not in self.metadata._get_tikr(tikr)['submissions']:
                    self.metadata.initialize_submission_metadata(tikr, fname)
                self.metadata._get_submission(tikr, fname)['attrs'][
                    'is_ims-document'] = True
                self.metadata._get_submission(tikr, fname)['attrs'][
                    'FORM TYPE'] = 'IMS'
                return
        d = p
        if d is None:
            warnings.warn('No sec-document tag found in submission',
                          RuntimeWarning)
            return

        documents = d.find_all('document', recursive=False)

        self._gen_tikr_metadata(tikr, documents, fname)

        sec_header = d.find('sec-header').text.replace('\t', '').split('\n')
        sec_header = [i for i in sec_header if ':' in i]
        attrs = {i.split(':')[0]: i.split(':')[1] for i in sec_header}
        self.metadata._get_tikr(tikr)['submissions'][fname]['attrs'] = attrs

        # We track whether any submission is succesfully unpacked
        non_empty = False
        for doc in documents:
            non_empty = non_empty or self.__unpack_doc__(
                tikr, fname, doc, document_type=document_type, force=force,
                include_supplementary=include_supplementary)

        if remove_raw:
            os.remove(os.path.join(d_dir, file))
            self.metadata.set_downloaded(tikr, False)

            # Metadata only exists for submission that has entries unpacked
            if non_empty:
                self.metadata._gen_submission_metadata(tikr, file.replace(
                    '.txt', ''))

        self.metadata.save_tikr_metadata(tikr)

    def _are_filings_unpacked(self, tikr: str, document_type: str):
        """
        Get whether filings for a given company have been unpacked.

        Parameters
        ----------
        tikr: str
            The queried company stock ticker
        document_type: str or DocumentType
            The type of filings in question
        """
        return self.metadata._get_tikr(tikr)['attrs'].get(
            f'{document_type}_extracted', False)

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
            force_remove_raw=False,
            document_type='all', silent=False,
            include_supplementary=False):
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
        loading_bar: bool
            if True, will time and show progress
        document_type: str or DocumentType
            The type of filings in question
        remove_raw: bool, Optional
            If True, will delete each raw file after it is extracted
        force_remove_raw: bool, Optional
            If True, will delete all files in the unpacking directory
            even if some are not unpacked.
        include_supplementary: bool = False
            If (True), then load all supplementary material as well.
        """
        document_type = DocumentType(document_type)
        if document_type == 'all':
            self.unpack_bulk(tikr, force=force, loading_bar=False,
                             desc=desc, remove_raw=remove_raw,
                             document_type='10-Q', silent=silent,
                             include_supplementary=include_supplementary)
            self.unpack_bulk(tikr, force=force, loading_bar=False,
                             desc=desc, remove_raw=remove_raw,
                             document_type='8-K', silent=silent,
                             include_supplementary=include_supplementary)
            return

        if force_remove_raw:
            remove_raw = True

        # Early quitting conditions
        if not force and self.metadata.is_unpacked(tikr, document_type):
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
                remove_raw=remove_raw,
                include_supplementary=True)

        # Delete raw files if desired
        d_dir = os.path.join(self.raw_dir, f'{tikr}', f'{document_type}')

        if force_remove_raw:
            if os.path.exists(d_dir):
                for file in os.listdir(d_dir):
                    os.remove(os.path.join(d_dir, file))

        if (remove_raw and os.path.exists(d_dir) and
                len(os.listdir(d_dir)) == 0):

            os.rmdir(d_dir)
            # If all filings have now been removed, clean up tikr directory
            parent_dir = os.path.join(self.raw_dir, f'{tikr}')
            if len(os.listdir(parent_dir)) == 0:
                os.rmdir(parent_dir)
                if len(os.listdir(self.raw_dir)) == 0:
                    os.rmdir(self.raw_dir)

        # TODO if we unpack 10-q then 8-k we should have all unpacked
        self.metadata.set_unpacked(
            tikr, document_type=document_type, value=True)

        self.metadata.save_tikr_metadata(tikr)

    def get_dates(self, tikr, **kwargs):
        """Return the filing submission txt closest to provided date."""
        out = dict()
        for i in self.get_submissions(
            tikr, document_type=kwargs.get(
                'document_type', 'all')):
            date_str = self.metadata._get_submission(tikr, i)['attrs'].get(
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
