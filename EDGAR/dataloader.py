"""
Downloads 10-Q filings from SEC website
Extracts 10-Q htm files from these filing txt dumps
"""
from secedgar import filings, FilingType
from secedgar.exceptions import NoFilingsError
from bs4 import BeautifulSoup
from yaml import load, CLoader as Loader
import pickle as pkl


import os
import warnings
import datetime
import time
import sys
from tqdm.auto import tqdm 


from metadata_manager import metadata_manager


class edgar_dataloader:
    def __init__(self, metadata = None, 
                 data_dir = 'default',
                 api_keys_path = 'default'):

        if data_dir == 'default':
            data_dir = 'edgar_downloads'
        self.data_dir = os.path.join(data_dir, '')

        # our HTML files are so big and nested that the standard
        #   1000 limit is too small.
        sys.setrecursionlimit(10000)

        # Always gets the path of the current file
        self.path = os.path.abspath(os.path.join(__file__, os.pardir))

        # Loads keys
        if api_keys_path == 'default':
            api_keys_path = os.path.join('..','api_keys.yaml');
        key_path = os.path.join(self.path, api_keys_path)
        assert os.path.exists(api_keys_path), 'No api_keys.yaml located'
        self.apikeys = load(open(api_keys_path, 'rb'), Loader=Loader)
        assert 'edgar_email' in self.apikeys, 'Set personal email'
        assert 'edgar_agent' in self.apikeys, 'Set personal name'

        # Download and processed directories
        self.raw_dir = os.path.join(self.path, self.data_dir, 'raw')
        self.proc_dir = os.path.join(self.path, self.data_dir, 'processed')

        if metadata is None:
            self.metadata = metadata_manager(data_dir=data_dir);
        else:
            self.metadata = metadata

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

    # Returns True if TIKR had previous bulk download
    def _is_downloaded(self, tikr):
        return self.metadata[tikr]['attrs'].get('downloaded', False)

    def query_server(
            self, tikr, start_date=None, end_date=None, max_num_filings=None,
            filing_type=FilingType.FILING_10Q, force=False):

        if self._is_downloaded(tikr) and not force:
            print('\talready downloaded')
            return

        elif (start_date is None and end_date is None and
            max_num_filings is None
            ):

            self.metadata[tikr]['attrs']['downloaded'] = True
            self.metadata.save_tikr_metadata(tikr)

        user_agent = "".join([f"{self.apikeys['edgar_agent']}", 
                              f": {self.apikeys['edgar_email']}"])
        f = filings(cik_lookup=tikr,
                    filing_type=filing_type,
                    count=max_num_filings,
                    user_agent=user_agent,
                    start_date=start_date,
                    end_date=end_date)

        # Beautiful Soup parsing XML as HTML error
        #   (Ignored because we are using iXML HTML markup)
        warnings.simplefilter('ignore')
        f.save(self.raw_dir)
        warnings.simplefilter('default')

    """
        Utility Function
        Get list of targets for unpack_file func
    """
    def get_unpackable_files(self, tikr):
        # sec-edgar data save location for 10-Q filing ticker
        d_dir = os.path.join(self.raw_dir,f'{tikr}', '10-Q')
        return os.listdir(d_dir)
    
    """
        Utility Function
        Get list of submissions under ticker
    """
    def get_submissions(self, tikr):
        # sec-edgar data save location for 10-Q filing ticker
        return [i.split('.txt')[0] for i in self.get_unpackable_files(tikr)]

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

        # Only Unpack 10-Q HTM if not complete unpacking
        if not complete and form_type not in {"FORM 10-Q", "10-Q"}:
            return

        fname = metadata[sequence]['filename']

        with open(os.path.join(out_path, fname), 'w', encoding='utf-8') as f:
            f.write(doc.prettify())
            metadata[sequence]['processed'] = True

    """
        Processes raw data from one filing at one company;
            See utility function for getting file names;

        Str: tikr - company ticker associated with unpacking

        Str: filename - filing submission to unpack

        Bool: complete - If False, only unpacks 10-Q, otherwise all documents.

        Bool: force - if True, will unpack and overwrite previously unpacked do
    """
    def unpack_file(self, tikr, file, complete=True, force=True):

        # sec-edgar data save location for 10-Q filing ticker
        d_dir = os.path.join(self.raw_dir, f'{tikr}', '10-Q')

        content = None
        with open(d_dir + file, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        d = BeautifulSoup(content, features='lxml').body

        p = d.find('sec-document')
        if p is None:
            p = d.find('ims-document')
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
    
    def _is_fully_unpacked(self, tikr):
        return self.metadata[tikr]['attrs'].get('complete_unpacked', False)

    """
        Processes all raw data from one company;

        Str: tikr - company ticker associated with unpacking

        Bool: complete - If False, only unpacks 10-Q, otherwise all documents.

        Bool: force - if True will unpack and overwrite previously unpacked doc

        Bool: loading__bar - if True, will time and show progress
    """
    def unpack_bulk(
            self, tikr, complete=False, force=False,
            loading_bar=False, desc='Inflating HTM'):

        # Early quitting conditions
        if not force:
            if self._is_10q_unpacked(tikr):
                if not complete or self._is_fully_unpacked(tikr):
                            return

        # sec-edgar data save location for 10-Q filing ticker
        d_dir = os.path.join(self.raw_dir, f'{tikr}', '10-Q')

        # Read each text submission dump for each quarterly filing
        files = self.get_unpackable_files(tikr)

        itera = files
        if loading_bar:
            itera = tqdm(itera, desc=desc, leave=False)

        for file in itera:
            self.unpack_file(tikr, file, complete=complete, force=force)
 
        # Metadata tags to autoskip this bulk unpack later
        self.metadata[tikr]['attrs']['10q_unpacked'] = True
        if complete:
            self.metadata[tikr]['attrs']['complete_unpacked'] = True

        self.metadata.save_tikr_metadata(tikr)

    def get_dates(self, tikr):
        out = dict()
        for i in self.get_submissions(tikr):
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
            self, date, tikr, return_date=False, prefer_recent=True):

        # Provide AAAABBCC format (Year, Month, Day) with 0 padding
        if type(date) is str:
            assert len(date) == 8, 'String format wrong'
            date = datetime.datetime.strptime(date, '%Y%m%d')
        assert type(date) is datetime.datetime, 'Wrong format'

        dates = self.get_dates(tikr)
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

    """
        Returns 10-q filename associated with submission
    """
    def get_10q_name(self, filename, tikr):
        meta = self.metadata[tikr]['submissions'][filename]['documents']
        for file in meta:
            if meta[file]['type'] in ['10-Q', 'FORM 10-Q']:
                return meta[file]['filename']

    def __del__(self):
        # back to normal
        sys.setrecursionlimit(1000)


# Test example
loader = None
if __name__ == '__main__':

    loader = edgar_dataloader(data_dir='edgar_downloads')
    tikrs = ['nflx']

    max_num_filings = 3
    start_date = datetime.datetime(2020, 1, 15)
    end_date = datetime.datetime(2023, 7, 15)

    # If we set all to None, we get everything
    #    Metadata will note this and prevent re-pulling
    max_num_filings = None
    start_date = None
    end_date = None

    for tikr in tikrs:
        time.sleep(1)
        loader.metadata.load_tikr_metadata(tikr)

        print("First we download...")
        loader.query_server(tikr, start_date, end_date, max_num_filings)
        print("Look: if we try again it declines;")
        loader.query_server(tikr, start_date, end_date, max_num_filings)
        print("""Now we unpack all tikr filings in bulk locally
        but only for the 10-Q...""")
        loader.unpack_bulk(tikr, loading_bar=True)
        print("""We can also unpack individual files more thoroughly
                , i.e. for supporting figures.""")
        files = loader.get_unpackable_files(tikr)
        print(f"Here is one: {files[0]}")
        print("We are unpacking it...")
        loader.unpack_file(tikr, files[0], complete=False)
        print("All done!")
