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
    



class edgar_dataloader:
    def __init__(self, data_dir='edgar_downloads/',
                 api_keys_path='../api_keys.yaml'):

        self.data_dir = data_dir

        # our HTML files are so big and nested that the standard
        #   1000 limit is too small.
        sys.setrecursionlimit(5000)

        # Always gets the path of the current file
        self.path = os.path.abspath(os.path.join(__file__, os.pardir))
        # Loads keys
        key_path = os.path.join(self.path, api_keys_path)
        assert os.path.exists(api_keys_path), 'No api_keys.yaml located'
        self.apikeys = load(open(api_keys_path, 'rb'), Loader=Loader)
        assert 'edgar_email' in self.apikeys, 'Set personal email'
        assert 'edgar_agent' in self.apikeys, 'Set personal name'

        # Download and processed directories
        self.raw_dir = os.path.join(self.path, self.data_dir, 'raw')
        self.proc_dir = os.path.join(self.path, self.data_dir, 'processed')

        self.metadata = dict()

    def __load_metadata__(self, tikr):

        data_path = os.path.join(self.proc_dir, f"{tikr}/metadata.pkl")

        if os.path.exists(data_path):
            with open(data_path, 'rb') as f:
                self.metadata[tikr] = pkl.load(f)

    def __save_metadata__(self, tikr):

        path = os.path.join(
                    self.proc_dir, f"{tikr}/metadata.pkl"
                    )

        ensure_path = os.path.join(self.proc_dir, str(tikr))
        if not os.path.exists(ensure_path):
            os.system('mkdir -p ' + ensure_path)

        with open(path, 'wb') as f:
            pkl.dump(self.metadata[tikr], f)

    def __gen_metadata__(self, tikr, documents, key):
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
        if tikr not in self.metadata:
            self.metadata[tikr] = dict()

        if key not in self.metadata[tikr]:
            self.metadata[tikr][key] = {'documents': out}
        else:
            self.metadata[tikr][key]['documents'] = \
                    dict(out, **self.metadata[tikr][key]['documents'])

    # Returns True if TIKR had previous bulk download
    def __check_downloaded__(self, tikr):
        self.__load_metadata__(tikr)
        if tikr not in self.metadata:
            self.metadata[tikr] = dict()
        if 'downloaded' not in self.metadata[tikr]:
            self.metadata[tikr]['downloaded'] = False
        if self.metadata[tikr]['downloaded']:
            return True
        return False

    def __query_server__(
            self, tikr, start_date=None, end_date=None, max_num_filings=None,
            filing_type=FilingType.FILING_10Q, force=False):

        if self.__check_downloaded__(tikr) and not force:
            print('\talready downloaded')
            return

        elif (start_date is None and end_date is None and
            max_num_filings is None
            ):

            self.metadata[tikr]['downloaded'] = True
            self.__save_metadata__(tikr)

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
        d_dir = os.path.join(self.raw_dir,f'{tikr}', '10-Q')
        return [i.split('.txt')[0] for i in os.listdir(d_dir)]

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

        with open(os.path.join(out_path, fname), 'w') as f:
            f.write(doc.prettify(), encoding='utf-8')
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

        # Look at metadata to see if files have been unpacked
        self.__load_metadata__(tikr)

        # sec-edgar data save location for 10-Q filing ticker
        d_dir = self.raw_dir+f'/{tikr}/10-Q/'

        content = None
        with open(d_dir + file, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        d = BeautifulSoup(content, features='lxml').body

        p = d.find('sec-document')
        if p is None:
            p = d.find('ims-document')
            print('Skipping ims-document')
            return
        d = p
        assert d is not None, 'No sec-document tag found in submission'

        documents = d.find_all('document', recursive=False)

        fsub = file.split('.txt')[0]
        self.__gen_metadata__(tikr, documents, fsub)

        sec_header = d.find('sec-header').text.replace('\t', '').split('\n')
        sec_header = [i for i in sec_header if ':' in i]
        sec_attrs = {i.split(':')[0]: i.split(':')[1] for i in sec_header}
        self.metadata[tikr][fsub]['sec_attrs'] = sec_attrs

        metadata = self.metadata[tikr][fsub]['documents']

        # Processed data directory path
        out_path = os.path.join(
            self.path, 'edgar_downloads/processed/',
            tikr, file.split('.txt')[0])
        if not os.path.exists(out_path):
            os.system('mkdir -p ' + out_path)

        for doc in documents:
            self.__unpack_doc__(
                doc, metadata, out_path, complete=complete, force=force)
        self.__save_metadata__(tikr)

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

        # Look at metadata to see if files have been unpacked
        self.__load_metadata__(tikr)

        # sec-edgar data save location for 10-Q filing ticker
        d_dir = os.path.join(self.raw_dir, f'{tikr}', '10-Q')

        # Read each text submission dump for each quarterly filing
        files = self.get_unpackable_files(tikr)

        itera = files
        if loading_bar:
            itera = tqdm(itera, desc=desc, leave=False)

        for file in itera:
            self.unpack_file(tikr, file, complete=complete, force=force)

        self.__save_metadata__(tikr)

    def get_dates(self, tikr):
        out = dict()
        for i in self.get_submissions(tikr):
            date_str = self.metadata[tikr][i]['sec_attrs'].get(
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

    def get_10q_name(self, filename, tikr):
        meta = self.metadata[tikr][filename]['documents']
        for file in meta:
            if meta[file]['type'] in ['10-Q', 'FORM 10-Q']:
                return meta[file]['filename']

    def __del__(self):
        # back to normal
        sys.setrecursionlimit(1000)


# Test example
loader = None
if __name__ == '__main__':

    loader = edgar_dataloader('edgar_downloads')
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

        print("First we download...")
        loader.__query_server__(tikr, start_date, end_date, max_num_filings)
        print("Look: if we try again it declines;")
        loader.__query_server__(tikr, start_date, end_date, max_num_filings)
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
