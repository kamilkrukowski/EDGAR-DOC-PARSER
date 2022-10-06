from yaml import load, CLoader as Loader
import os

path = os.path.abspath(os.path.join(__file__, os.pardir))

apikeys = load( open(os.path.join(path,'../api_keys.yaml'),
                    'rb'), Loader=Loader)

assert 'edgar_email' in apikeys, 'Set email';
assert 'edgar_agent' in apikeys, 'Set email';

data_dir = os.path.join(path, 'edgar_downloads')

import json


fil = './nflx/10-Q/0001065280-22-000257/'
meta_f = '0.metadata.json' 

oldf = './nflx/10-Q/0001193125-06-167595/0.metadata.json'

def load_metadata(fil):
    meta_f = '0.metadata.json' 
    m = None;
    with open(os.path.join(fil, meta_f), 'rb') as f:
        m = json.load(f)
    return m;

def get_names(fil, filetype='10-Q'):
    
    if filetype is not set:
        if filetype is not list:
            filetype = [filetype]
        filetype = set(filetype)
    
    meta = load_metadata(fil);
    
    out = [];
    for document in meta['documents']:
        if document['type'] in filetype:
            out.append(document['filename'])

    return out;

def get_metadata(fil, keys=False):
    files = [i for i in os.listdir(fil) if '.txt' not in i]
    metas = [load_metadata(os.path.join(fil,i)) for i in files] 
    for meta, filename in zip(metas, files):
        meta['FILENAME'] = filename
    #    return {i:meta for (meta, i) in zip(metas, files)}
    if not keys:
        return { meta['CONFORMED_PERIOD_OF_REPORT']:meta for meta in metas }
    else:
        out = { meta['CONFORMED_PERIOD_OF_REPORT']:meta for meta in metas }
        keys = sorted(list(out.keys()), key=lambda x: int(x))
        return out, keys;

def get_text(html):
    return BeautifulSoup(html, features='html.parser').get_text();

def load_10q(filing):
    f = get_names(filing)[0]
    return get_text(open(os.path.join(filing, '0.'+f)).read())


docs = get_names(fil);
fp = './nflx/10-Q'
meta, k = get_metadata('./nflx/10-Q', keys=True)

early = k[0]
late = k[-1]

use = early

docname = meta[use]['documents'][0]['filename']
p = meta[use]['FILENAME']
path = os.path.join(fp, p, '0.'+ docname)
f = open(path, 'r').read()

import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd


import itertools

driver = webdriver.Firefox()
html_content=f

html_bs64 = base64.b64encode(html_content.encode('utf-8')).decode()
driver.get("data:text/html;base64," + html_bs64)


found = driver.find_elements(By.TAG_NAME, 'font')
t = found[0]

texts = [];
tags = ['b', 'strong', 'p', 'i', 'em', 'mark', 'small', 'del', 'ins', 'sub', 'sup']
tags = set(tags)

temp = [i for i in found if i.text not in set([' ', ''])]

def border(elem, driver):
    driver.execute_script(f"arguments[0].setAttribute(arguments[1], arguments[2])", elem, "style", "padding: 1px; border: 2px solid red; display: inline-block")

for i in temp:
    border(i, driver);

#tables = [i.get_attribute('innerHTML') for i in driver.find_elements(By.TAG_NAME, 'table')]


