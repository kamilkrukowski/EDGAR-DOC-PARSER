"""
Downloads 10-Q filings from SEC website
Extracts 10-Q htm files from these filing txt dumps
"""
from secedgar import filings, FilingType
from bs4 import BeautifulSoup
from yaml import load, CLoader as Loader


import os
import datetime
import time
import sys

# Always gets the path of the current file
path = os.path.abspath(os.path.join(__file__, os.pardir))

class edgar_dataloader:
    
    def __init__(self, data_dir = 'edgar_downloads/'):
        
        self.data_dir = data_dir
        
        # our HTML files are so big and nested that the standard
        #   1000 limit is too small.
        sys.setrecursionlimit(3000);

        # Always gets the path of the current file
        self.path = os.path.abspath(os.path.join(__file__, os.pardir))
        
        # Loads keys
        key_path = os.path.join(path,'../api_keys.yaml')
        assert os.path.exists(key_path), 'No api_keys.yaml in parent dir';
        self.apikeys = load( open(key_path, 'rb'), Loader=Loader)
        assert 'edgar_email' in self.apikeys, 'Set personal email';
        assert 'edgar_agent' in self.apikeys, 'Set personal name';

        # Download and processed directories
        self.raw_dir = os.path.join(self.path, self.data_dir, 'raw')
        self.proc_dir = os.path.join(self.path, self.data_dir, 'processed')


    def __query_server__(self, tikr, start_date=None, end_date=None, max_num_filings=None, filing_type=FilingType.FILING_10Q):

        #TODO ADD CHECK/METADATA for whether it has been pulled already
        #   STRATEGY: enumerate all filing dates in metadata file
        f = filings(cik_lookup=tikr,
                    filing_type=filing_type,
                    count=max_num_filings,
                    user_agent=f"{self.apikeys['edgar_agent']}: {self.apikeys['edgar_email']}",
                    start_date=start_date,
                    end_date=end_date)

        f.save(self.raw_dir)

    """
        Processes raw data;
        Takes bulk .txt archive submission from SEC-DOWNLOAD
        unpacks into individual files in processed directory

        Bool: Complete - If False, only unpacks 10-Q, otherwise all documents.

    """
    def __unpack_bulk__(self, tikr, complete=False):
        
        # sec-edgar data save location for 10-Q filing ticker
        d_dir = self.raw_dir+f'/{tikr}/10-Q/'


        # Read each text submission dump for each quarterly filing
        files = os.listdir(d_dir)
        for file in files:
            
            content = None
            with open(d_dir + files[0],'r') as f:
                content = f.read().strip();

            d = BeautifulSoup(content, features='lxml').body
            assert len(list(d.children)) == 1, 'sec-document child';
            d = [i for i in d.children][0]

            documents = d.find_all('document', recursive=False)

            # Processed data directory path
            out_path = os.path.join(path, 'edgar_downloads/processed/', tikr, file.split('.txt')[0])
            if not os.path.exists(out_path):
                os.system('mkdir -p ' + out_path)

            for doc in documents:
                fname = list(doc.find('filename').children)[0].text.strip('\n')    
                form_type = list(doc.find('description').children)[0].text.strip('\n')    
                
                # Only Unpack 10-Q HTM if not complete unpacking
                if not complete and form_type not in {"FORM 10-Q", "10-Q"}:
                    continue;

                with open(os.path.join(out_path, fname), 'w') as f:
                    f.write(doc.prettify())


    def __del__(self):
        #back to normal
        sys.setrecursionlimit(1000);

loader = edgar_dataloader('edgar_downloads');
tikrs=['nflx'];
max_num_filings=3;
start_date=datetime.date(2022, 1, 30)
end_date=datetime.date(2023, 10, 30)

for tikr in tikrs:
    time.sleep(1)

    loader.__query_server__(tikr, start_date, end_date, max_num_filings)
    loader.__unpack_bulk__(tikr)
