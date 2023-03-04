import re
import sys
from bs4 import BeautifulSoup

sys.path.append('src')
import edgar
import edgar.html as html
from edgar.subheader_parser_8k import Parser_8K 

DATA_DIR = '8kdata'
DELETE_RAW = False

tikrs = ['aapl', 'msft', 'amzn', 'tsla', 'googl', 'goog',  'unh', 'jnj', 'cvx',
         'jpm', 'hd', 'v', 'pg']
metadata = edgar.Metadata(data_dir=DATA_DIR)
kparser = Parser_8K();

items = ['termination of a material definitive agreement',
         'change in credit enhancement or other external support',
         'shareholder director nominations',
         'acquisition or disposition of assets',
         'unregistered sales of equity securities',
         'material impairments',
         "resignations of registrant's directors",
         'changes in control of registrant',
         "amendment to registrant's code of ethics, or waiver of a provision of the code of ethics",
         'regulation fd disclosure',
         'completion of acquisition or disposition of assets',
         'triggering events that accelerate or increase a direct financial obligation or an obligation under an off-balance sheet arrangement',
         'non-reliance on previously issued financial statements or a related audit report or completed interim review',
         "changes in registrant's certifying accountant",
         'material modifications to rights of security holders',
         'departure of directors or certain officers; election of directors; appointment of certain officers; compensatory arrangements of certain officers',
         'other events',
         'change of servicer or trustee',
         'failure to make a required distribution',
         'material modification to rights of security holders',
         'cost associated with exit or disposal activities',
         'securities act updating disclosure',
         'financial statements and exhibits',
         'results of operations and financial condition',
         'abs informational and computational material',
         'entry into a material definitive agreement',
         'notice of delisting or failure to satisfy a continued listing rule or standard; transfer of listing',
         'creation of a direct financial obligation or an obligation under an off-balance sheet arrangement of a registrant',
         'amendments to articles of incorporation or bylaws; change in fiscal year',
         'mine safety - reporting of shutdowns and patterns of violations',
         'change in shell company status',
         'submission of matters to a vote of security holders',
         'bankruptcy or receivership',
         "temporary suspension of trading under registrant's employee benefit plans",
         "amendments to the registrant's code of ethics, or waiver of a provision of the code of ethics"]

data = []
f = None
for tikr in tikrs:
    print(tikr)
    edgar.load_files(tikr, data_dir=DATA_DIR, document_type='8-K',
                     include_supplementary=False, force_remove_raw=DELETE_RAW)

    submissions = metadata.get_submissions(tikr)
    for sub in submissions:
        files = edgar.get_files(tikrs=tikr, submissions=sub, metadata=metadata)

        # Store consecutive supplementary file contents as text stream to
        # concatenate later.
        out = []
        for file in files:
            # Skip unextracted files
            if not metadata._get_file(tikr, sub, file).get('extracted', False):
                continue

            f1 = edgar.read_file(tikr, sub, file, document_type='8-K',
                                 data_dir=DATA_DIR)
            
            kparser.get_sections(f)