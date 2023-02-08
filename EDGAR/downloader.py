from secedgar import filings, FilingType
from bs4 import BeautifulSoup


import os
import pathlib
import warnings
import datetime
import sys
from tqdm.auto import tqdm 


from .metadata_manager import metadata_manager


class edgar_downloader:
    """
        Class for querying SEC-EDGAR database for files
    """
    def __init__(self, data_dir, metadata = None):

        # our HTML files are so big and nested that the standard
        #   1000 limit is too small.
        sys.setrecursionlimit(10000000)

        # Always gets the path of the current file
        self.path = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
        self.data_dir = os.path.join(self.path, data_dir)
        if metadata is None:
            self.metadata = metadata_manager(data_dir=data_dir);
        else:
            self.metadata = metadata

        # Loads keys
        self.metadata.load_keys();

        if 'edgar_email' not in self.metadata.keys or 'edgar_agent' not in self.metadata.keys:
            print(f"No API Header detected.\nThe SEC requires all EDGAR API users to identify themselves\n\n")
            if 'edgar_agent' not in self.metadata.keys:
               print("The SEC requires a legal name of the user and any organizational affiliation")
               answer = 'n'
               while (answer[0] != 'y' or len(answer) > 4):
                    self.metadata.keys['edgar_agent'] = input("User(s): ")
                    answer = input(f"Input User(s) \'{self.metadata.keys['edgar_agent']}\'\n Is this correct? (y/n)")
            if 'edgar_email' not in self.metadata.keys:
               print("The SEC requires a contact email for the API user")
               answer = 'n'
               while (answer[0] != 'y' or len(answer) > 4):
                    self.metadata.keys['edgar_email'] = input("Email: ")
                    answer = input(f"Input Email \'{self.metadata.keys['edgar_email']}\'\n Is this correct? (y/n)")
            self.metadata.save_keys()

        assert 'edgar_email' in self.metadata.keys, 'Set personal email'
        assert 'edgar_agent' in self.metadata.keys, 'Set personal name'

        # Download and processed directories
        self.raw_dir = os.path.join(self.path, self.data_dir, 'raw')
        self.proc_dir = os.path.join(self.path, self.data_dir, 'processed')

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
                
                #Sentinel for missing fields in early 2000s
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
        """

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
        f = filings(cik_lookup=tikr,
                    filing_type=kwargs.get('filing_type', None),
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
                document type to unpack (10-Q, 8-K, or all)

        """
        # sec-edgar data save location for documents filing ticker
        if kwargs.get('document_type', '10-Q') == '10-Q':
            d_dir = os.path.join(self.raw_dir, f'{tikr}', '10-Q')
        elif kwargs.get('document_type', '10-Q') == '8-K':
            d_dir = os.path.join(self.raw_dir, f'{tikr}', '8-K')
        else:
            d_dir = os.path.join(self.raw_dir, f'{tikr}', 'all-documents')
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
        return [i.split('.txt')[0] for i in self.get_unpackable_files(tikr, document_type=kwargs.get('document_type', '10-Q'))]

    """
        Private utility, parses SEC submission dump into components
    """
    def __unpack_doc__(
            self, doc, metadata, out_path, complete=True, force=True):

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
        if not complete and form_type not in {"FORM 10-Q", "10-Q", "FORM 8-K", "8-K"}:
            return

        fname = metadata[sequence]['filename']

        with open(os.path.join(out_path, fname), 'w', encoding='utf-8') as f:
            f.write(doc.prettify())
            metadata[sequence]['processed'] = True

    def unpack_file(self, tikr, file, complete=True, force=True, **kwargs):
        """
            Processes raw data from one filing at one company;
                See utility function for getting file names;

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
                if (True), then ignore locally downloaded files and overwrite them. Otherwise, attempt to detect previous download and abort server query.
        """

        # sec-edgar data save location for documents filing ticker
        if complete == False:
            if kwargs.get('document_type', '10-Q') =='10-Q':
                d_dir = os.path.join(self.raw_dir, f'{tikr}', '10-Q')
            elif kwargs.get('document_type', '10-Q') == '8-K':
                d_dir = os.path.join(self.raw_dir, f'{tikr}', '8-K')
        else:
            d_dir = os.path.join(self.raw_dir, f'{tikr}', 'all-documents')


        content = None
        with open(os.path.join(d_dir, file), 'r', encoding='utf-8') as f:
            content = f.read().strip()

        d = BeautifulSoup(content, features='lxml').body

        p = d.find('sec-document')
        if p is None:
            p = d.find('ims-document')
            if p is not None:
                warnings.warn("IMS-DOCUMENT skipped during loading", RuntimeWarning)
                fname = file.split('.txt')[0]
                if fname not in self.metadata[tikr]['submissions']:
                    self.metadata.initialize_submission_metadata(tikr, fname)
                self.metadata[tikr]['submissions'][fname]['attrs']['is_ims-document'] = True
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
            self.path, self.data_dir, 'processed',
            tikr, file.split('.txt')[0])
        if not os.path.exists(out_path):
            os.system('mkdir -p ' + out_path)

        for doc in documents:
            self.__unpack_doc__(
                doc, metadata, out_path, complete=complete, force=force)
        self.metadata.save_tikr_metadata(tikr)

    def _is_10q_unpacked(self, tikr):
        return self.metadata[tikr]['attrs'].get('10q_unpacked', False)

    def _is_8k_unpacked(self, tikr):
        return self.metadata[tikr]['attrs'].get('8k_unpacked', False)
    
    def _is_fully_unpacked(self, tikr):
        return self.metadata[tikr]['attrs'].get('complete_unpacked', False)

    def unpack_bulk(
            self, tikr, complete=True, force=False,
            loading_bar=False, desc='Inflating HTM', **kwargs):
        """
            Processes all raw data from one company
            
            Parameters
            ---------
            tikr: str
                company ticker associated with unpacking
            complete: bool
                If False, only unpacks 10-Q or 8-K, otherwise all documents.
            force: bool
                if (True), then ignore locally downloaded files and overwrite them. Otherwise, attempt to detect previous download and abort server query.
            loading__bar: bool:
                if True, will time and show progress
        """

        # Early quitting conditions
        if not force:
            if self._is_10q_unpacked(tikr) or self._is_8k_unpacked(tikr):
                if not complete or self._is_fully_unpacked(tikr):
                            return


        # Read each text submission dump for each quarterly filing
        files = self.get_unpackable_files(tikr, document_type=kwargs.get('document_type', '10-Q'))
        print("files to unpack", files)

        itera = files
        if loading_bar:
            itera = tqdm(itera, desc=desc, leave=False)

        for file in itera:
            self.unpack_file(tikr, file, complete=complete, document_type=kwargs.get('document_type', '10-Q'), force=force)
 
        # Metadata tags to autoskip this bulk unpack later
        self.metadata[tikr]['attrs']['10q_unpacked'] = True
        if complete:
            self.metadata[tikr]['attrs']['complete_unpacked'] = True

        self.metadata.save_tikr_metadata(tikr)

    def get_dates(self, tikr,  **kwargs):
        out = dict()
        for i in self.get_submissions(tikr, document_type=kwargs.get('document_type', '10-Q')):
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
        if type(date) is str:
            assert len(date) == 8, 'String format wrong'
            date = datetime.datetime.strptime(date, '%Y%m%d')
        assert type(date) is datetime.datetime, 'Wrong format'

        dates = self.get_dates(tikr, document_type=kwargs.get('document_type', '10-Q'))
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
