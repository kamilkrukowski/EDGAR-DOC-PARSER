from secedgar import filings, FilingType
from bs4 import BeautifulSoup


import os
import pathlib
import warnings
import datetime
import sys
from tqdm.auto import tqdm
from time import sleep



from metadata_manager import metadata_manager


class edgar_downloader:
    """
        Class for querying SEC-EDGAR database for files
    """

    def __init__(self, data_dir, metadata):

        # our HTML files are so big and nested that the standard
        #   1000 limit is too small.
        sys.setrecursionlimit(10000000)

        # Always gets the path of the current file
        self.data_dir = data_dir
        # Download and processed directories
        self.raw_dir = os.path.join(self.data_dir, 'raw')
        self.proc_dir = os.path.join(self.data_dir, 'processed')

        self.metadata = metadata

        # Loads keys
        self.metadata.load_keys()

        if 'edgar_email' not in self.metadata.keys or 'edgar_agent' not in self.metadata.keys:
            print(
                f"No API Header detected.\nThe SEC requires all EDGAR API users to identify themselves\n\n")
            if 'edgar_agent' not in self.metadata.keys:
                print(
                    "The SEC requires a legal name of the user and any organizational affiliation")
                answer = 'n'
                while (answer[0] != 'y' or len(answer) > 4):
                    self.metadata.keys['edgar_agent'] = input("User(s): ")
                    answer = input(
                        f"Input User(s) \'{self.metadata.keys['edgar_agent']}\'\n Is this correct? (y/n)")
            if 'edgar_email' not in self.metadata.keys:
                print("The SEC requires a contact email for the API user")
                answer = 'n'
                while (answer[0] != 'y' or len(answer) > 4):
                    self.metadata.keys['edgar_email'] = input("Email: ")
                    answer = input(
                        f"Input Email \'{self.metadata.keys['edgar_email']}\'\n Is this correct? (y/n)")
            self.metadata.save_keys()

        assert 'edgar_email' in self.metadata.keys, 'Set personal email'
        assert 'edgar_agent' in self.metadata.keys, 'Set personal name'

    def _gen_tikr_metadata(self, tikr, documents, key):
        out = dict()

        for idx, doc in enumerate(documents):

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
                        out[seq][nextElem] = f"{seq}.htm"
                    else:
                        out[seq][nextElem] = ''
                    continue

                i = 20
                while ('\n') not in doc2.text[:i]:
                    i += 20
                out[seq][nextElem] = doc2.text[:i].split('\n')[0]

            out[seq]['processed'] = False

        # Extend existing tikr metadata with new results,
        #   or start with empty dict and add new results
        self.metadata.initialize_tikr_metadata(tikr)

        # Extending documents in existing submission or start new one
        self.metadata.initialize_submission_metadata(tikr, key)

        # Add documents to submission of tikr
        self.metadata[tikr]['submissions'][key]['documents'] = \
            dict(out, **self.metadata[tikr]['submissions'][key]['documents'])

    def _is_downloaded(self, tikr):
        """
            Returns True if TIKR had previous bulk download
        """
        return self.metadata[tikr]['attrs'].get('downloaded', False)

    def query_server(
            self, tikr: str, force: bool = False, **kwargs):
        """
            Download SEC filings to a local directory for later parsing, by company TIKR


            Parameters
            ---------
            tikr: str
                a company identifier to query
            force: bool
                if (True), then ignore locally downloaded files and overwrite them. Otherwise, attempt to detect previous download and abort server query.
            start_date: optional
                The earliest date to look for filings
            end_date: optional
                The latest filing date retrievable
            max_num_filings:
                The maximum number of documents to retrieve. Retrieves all documents if set to `None`.
            delay_time:
                The time (in seconds) delayed at the beginning of this function. 
        """
        sleep(kwargs.get('delay_time', 1))

        if self._is_downloaded(tikr) and not force:
            print('\talready downloaded')
            return

        elif (kwargs.get('start_date', None) is None and kwargs.get('end_date', None) is None and
              kwargs.get('max_num_filings', None) is None
              ):

            self.metadata[tikr]['attrs']['downloaded'] = True
            self.metadata.save_tikr_metadata(tikr)

        user_agent = "".join([f"{self.metadata.keys['edgar_agent']}",
                              f": {self.metadata.keys['edgar_email']}"])

        document_type = kwargs.get('document_type', '10-Q').replace('-',"").lower()
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

    def get_unpackable_files(self, tikr: str, **kwargs):
        """
            Get list of targets for unpack_file func

            Parameters
            ---------
            tikr: str
                a company identifier to query
            document_type: str
                document type to unpack (10-Q, 8-K)

        """
        # sec-edgar data save location for documents filing ticker
        document_type = kwargs.get(
            'document_type', 'all').replace('-', "").lower()
        assert document_type in {'all', '10q', '8k'}
        if document_type == '10q':
            d_dir = os.path.join(self.raw_dir, f'{tikr}', '10-Q')
        elif document_type == '8k':
            d_dir = os.path.join(self.raw_dir, f'{tikr}', '8-K')
        return os.listdir(d_dir)

    def get_submissions(self, tikr, **kwargs):
        """
            Get list of submissions under tikr

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

    """
        Private utility, parses SEC submission dump into components
    """

    def __unpack_doc__(
            self, doc, metadata, out_path, force=True):

        seq = doc.find('sequence')
        i = 20
        while ('\n') not in seq.text[:i]:
            i += 20
        sequence = seq.text[:i].split('\n')[0]

        processed = metadata[sequence]['processed']

        # Do not repeat work unless forcing
        if processed and not force:
            return

        form_type = metadata[sequence]['type']

        # Only Unpack 10-Q or 8-K HTM if not complete unpacking
        if form_type not in {"FORM 10-Q", "10-Q", "FORM 8-K", "8-K"}:
            return

        fname = metadata[sequence]['filename']

        with open(os.path.join(out_path, fname), 'w', encoding='utf-8') as f:
            f.write(doc.prettify())
            metadata[sequence]['processed'] = True

    def unpack_file(self, tikr, file, force=True, **kwargs):
        """
            Processes raw data from one filing at one company;
                See utility function for getting file names;

            Parameters
            ---------
            tikr: str
                company ticker associated with unpacking
            filename: str
                filing submission to unpack
            document_type: str
                document type to unpack (10-Q, 8-K, or all)
            force: bool
                if (True), then ignore locally downloaded files and overwrite them. Otherwise, attempt to detect previous download and abort server query.
            clean_raw: bool
                default to be true. If true, the raw data will be cleaned after parsed. 
        """

        # sec-edgar data save location for documents filing ticker
        document_type = kwargs.get('document_type', '10-Q').replace('-', "").lower()
        assert document_type in {'10q', '8k'}
        if document_type =='10q':
            d_dir = os.path.join(self.raw_dir, f'{tikr}', '10-Q')
        elif document_type == '8k':
            d_dir = os.path.join(self.raw_dir, f'{tikr}', '8-K')

        content = None
        with open(os.path.join(d_dir, file), 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if kwargs.get('clean_raw', True):
            os.remove(os.path.join(d_dir, file))

        d = BeautifulSoup(content, features='lxml').body

        p = d.find('sec-document')
        if p is None:
            p = d.find('ims-document')
            if p is not None:
                warnings.warn(
                    "IMS-DOCUMENT skipped during loading", RuntimeWarning)
                fname = file.split('.txt')[0]
                if fname not in self.metadata[tikr]['submissions']:
                    self.metadata.initialize_submission_metadata(tikr, fname)
                self.metadata[tikr]['submissions'][fname]['attrs'][
                    'is_ims-document'] = True
                return
        d = p
        assert d is not None, 'No sec-document tag found in submission'

        documents = d.find_all('document', recursive=False)

        fsub = file.split('.txt')[0]
        self._gen_tikr_metadata(tikr, documents, fsub)

        sec_header = d.find('sec-header').text.replace('\t', '').split('\n')
        sec_header = [i for i in sec_header if ':' in i]
        attrs = {i.split(':')[0]: i.split(':')[1] for i in sec_header}
        self.metadata[tikr]['submissions'][fsub]['attrs'] = attrs

        metadata = self.metadata[tikr]['submissions'][fsub]['documents']

        # Processed data directory path
        out_path = os.path.join(
            self.data_dir, 'processed',
            tikr, file.split('.txt')[0])
        if not os.path.exists(out_path):
            os.system('mkdir -p ' + out_path)

        for doc in documents:
            self.__unpack_doc__(
                doc, metadata, out_path, force=force)
        self.metadata.save_tikr_metadata(tikr)

    def _is_10q_unpacked(self, tikr):
        return self.metadata[tikr]['attrs'].get('10q_unpacked', False)

    def _is_8k_unpacked(self, tikr):
        return self.metadata[tikr]['attrs'].get('8k_unpacked', False)

    def _is_fully_unpacked(self, tikr):
        return self.metadata[tikr]['attrs'].get('complete_unpacked', False)

    def unpack_bulk(
            self, tikr, force=False,
            loading_bar=False, desc='Inflating HTM', **kwargs):
        """
            Processes all raw data from one company

            Parameters
            ---------
            tikr: str
                company ticker associated with unpacking
            force: bool
                if (True), then ignore locally downloaded files and overwrite them. Otherwise, attempt to detect previous download and abort server query.
            loading__bar: bool:
                if True, will time and show progress
            document_type:
            
        """

        # Early quitting conditions
        if not force:
            if self._is_10q_unpacked(tikr) or self._is_8k_unpacked(tikr):
                if self._is_fully_unpacked(tikr):
                            return


        # Read each text submission dump for each quarterly filing
        if kwargs.get('document_type', 'all') == 'all':
            files_8k = self.get_unpackable_files(tikr, document_type='8-K')
            files_10q = self.get_unpackable_files(tikr, document_type='10-Q')

            itera1 = files_8k
            itera2 = files_10q

            if loading_bar:
                itera1 = tqdm(itera1, desc=desc, leave=False)
            for file in itera1:
                self.unpack_file(tikr, file, document_type='8-K', force=force)
            if loading_bar:
                itera2 = tqdm(itera2, desc=desc, leave=False)
            for file in itera2:
                self.unpack_file(tikr, file, document_type='10-Q', force=force)

        else:
            files = self.get_unpackable_files(tikr, document_type=kwargs.get('document_type', '10-Q'))
            print("files to unpack", files)

            itera = files
            if loading_bar:
                itera = tqdm(itera, desc=desc, leave=False)

            for file in itera:
                self.unpack_file(tikr, file, document_type=kwargs.get('document_type', 'all'), force=force)
 
        # Metadata tags to autoskip this bulk unpack later
        if kwargs.get('document_type', 'all') == '10-Q':
            self.metadata[tikr]['attrs']['10q_unpacked'] = True
        elif kwargs.get('document_type', 'all') == '8-K':
            self.metadata[tikr]['attrs']['8k_unpacked'] = True
        else:
            self.metadata[tikr]['attrs']['all_unpacked'] = True

        self.metadata.save_tikr_metadata(tikr)

    def get_dates(self, tikr, **kwargs):
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

    """
        Return the filing submission txt closest to provided date
    """

    def get_nearest_date_filename(
            self, tikr, date, return_date=False, prefer_recent=True, **kwargs):
        """
        Gets the nearest date of the filename

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
        # back to normal
        sys.setrecursionlimit(1000)
