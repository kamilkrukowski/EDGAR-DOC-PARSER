"""
Downloads 10-Q filings from SEC website
Extracts 10-Q htm files from these filing txt dumps
"""
from secedgar import filings, FilingType
from bs4 import BeautifulSoup
from yaml import load, CLoader as Loader


import os
import datetime
import sys


# our HTML files are so big and nested that the standard
#   1000 limit is too small.
sys.setrecursionlimit(3000)

# Always gets the path of the current file
path = os.path.abspath(os.path.join(__file__, os.pardir))

# Loads keys
apikeys = load( open(os.path.join(path,'../api_keys.yaml'),
                    'rb'), Loader=Loader)
assert 'edgar_email' in apikeys, 'Set personal email';
assert 'edgar_agent' in apikeys, 'Set personal name';


data_dir = os.path.join(path, 'edgar_downloads/raw')
tikrs=['nflx'];
max_num_filings=3;
start_date=datetime.date(2022, 1, 30)
end_date=datetime.date(2023, 10, 30)

for tikr in tikrs:
    time.sleep(1)

    #TODO ADD CHECK/METADATA for whether it has been pulled already
    #   STRATEGY: enumerate all filing dates in metadata file
    f = filings(cik_lookup=tikr,
                filing_type=FilingType.FILING_10Q,
                count=max_num_filings,
                user_agent=f"{apikeys['edgar_agent']}: {apikeys['edgar_email']}",
                start_date=start_date,
                end_date=end_date)

    f.save(data_dir)
    
    # sec-edgar data save location for 10-Q filing ticker
    d_dir = data_dir+f'/{tikr}/10-Q/'


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
            
            # Only Unpack 10-Q HTM
            if form_type not in {"FORM 10-Q", "10-Q"}:
                continue;

            with open(os.path.join(out_path, fname), 'w') as f:
                f.write(doc.prettify())
