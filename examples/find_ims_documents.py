"""
    SEC-EDGAR has some very antiquated documents using
    'ims-document' tags in HTML unseen in all modern documents
    For now we have no way to process them...
        Our parsing just has to.... skip past them.

"""
from bs4 import BeautifulSoup


import os


import EDGAR

loader = EDGAR.downloader(data_dir=os.path.join('..','data'));

# List of companies to process
tikrs = open(os.path.join(loader.path, os.path.join('..','tickers.txt'))).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]

troublemakers= ['atvi:0000718877-95-000013.txt', 'k:0000055067-03-000251.txt'][1:]


for tikr in tikrs[6:]:
    files = loader.get_unpackable_files(tikr)
    print(f'\nTIKR is {tikr}\n')
    for file in files:
        print(f"Here is one: {file}")
        loader.unpack_file(tikr, file, complete=False)

assert 0, 'done'

d = None
p = None
documents = None
content = None
for t in troublemakers:
    t = t.split(':')
    tikr = t[0]
    fname = t[1]

    d_dir = os.path.join('.','edgar_downloads','raw',str(tikr),'10-Q')

    content = None
    with open(d_dir + fname, 'r') as f:
        content = f.read().strip()
    d = BeautifulSoup(content, features='lxml').body

    p = d.find('sec-document')
    if p is None:
        p = d.find('ims-document')
    d = p 
    assert type(d) is not None

    documents = d.find_all('document', recursive=False)

    fsub = fname.split('.txt')[0]
