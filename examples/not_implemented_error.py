import os
import sys ; sys.path.append('..')


from tqdm.auto import tqdm


import EDGAR


data_dir = os.path.join('..', 'data')

metadata = EDGAR.metadata(data_dir=data_dir)
loader = EDGAR.downloader(data_dir=data_dir);
parser = EDGAR.parser(data_dir=data_dir, metadata=metadata)

# List of companies to process
tikrs = open(os.path.join(loader.path, '..', 'tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]

labels = dict()
for tikr in tikrs:
    metadata.load_tikr_metadata(tikr)
    docs = metadata.get_submissions(tikr)

 
    for doc in tqdm(docs, desc=f"Processing {tikr}", leave=False):
        fname = metadata.get_10q_name(tikr, doc)

        # Try load cached, otherwise regenerate new file
        features = parser.featurize_file(tikr, doc, fname) 