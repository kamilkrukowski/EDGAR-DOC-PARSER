from yaml import load, CLoader as Loader
import os

path = os.path.abspath(os.path.join(__file__, os.pardir))

apikeys = load( open(os.path.join(path,'../api_keys.yaml'),
                    'rb'), Loader=Loader)

data_dir = os.path.join(path, 'edgar_downloads')

assert 'edgar_email' in apikeys, 'Set email';
assert 'edgar_agent' in apikeys, 'Set email';

from secedgar import filings, FilingType
from datetime import date

f = filings(cik_lookup='nflx',
            filing_type=FilingType.FILING_10Q,
            count=3,
            user_agent=f"{apikeys['edgar_agent']}: {apikeys['edgar_email']}")
f.save(data_dir)

d_dir = data_dir+'/nflx/10-Q/'
files = os.listdir(d_dir)

content = None
with open(d_dir + files[0],'r') as f:
    content = f.read().strip();

from bs4 import BeautifulSoup

d = BeautifulSoup(content, features='lxml').body
assert len(list(d.children)) == 1, 'sec-document child';

d = [i for i in d.children][0]
documents = d.find_all('document', recursive=False)

out_path = './'
for doc in documents:
    fname = list(doc.find('filename').children)[0].text.strip('\n')
    print(f"\'{fname}\'")
    with open(os.path.join(out_path, fname), 'w') as f:
        f.write(doc.prettify())
    break;
