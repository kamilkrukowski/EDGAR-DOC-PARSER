from yaml import load, CLoader as Loader
import os

path = os.path.abspath(os.path.join(__file__, os.pardir))

apikeys = load( open(os.path.join(path,'../api_keys.yaml'),
                    'rb'), Loader=Loader)

assert 'edgar_email' in apikeys, 'Set email';
assert 'edgar_agent' in apikeys, 'Set email';

data_dir = os.path.join(path, 'edgar_downloads')

import xbrl
import logging
from xbrl.cache import HttpCache
from xbrl.instance import XbrlParser, XbrlInstance
# just to see which files are downloaded
logging.basicConfig(level=logging.INFO)

cache: HttpCache = HttpCache('./cache')
cache.set_headers({'From': apikeys['edgar_email'], 'User-Agent': apikeys['edgar_agent']})
parser = XbrlParser(cache)

schema_url = "https://www.sec.gov/Archives/edgar/data/0000320193/000032019321000105/aapl-20210925.htm"
inst: XbrlInstance = parser.parse_instance(schema_url)

numerics = [str(i) for i in inst.facts if type(i) is xbrl.instance.NumericFact]

texts = [str(i) for i in inst.facts if type(i) is not xbrl.instance.NumericFact]
texts = sorted(texts, key=lambda x: len(x), reverse=True)
texts = [(len(i), i.split(':')[0], i) for i in texts]

from secedgar import filings, FilingType

f = filings(cik_lookup='nflx',
            filing_type=FilingType.FILING_10Q,
            user_agent=f"{apikeys['edgar_agent']}: {apikeys['edgar_email']}")
f.save('./')
