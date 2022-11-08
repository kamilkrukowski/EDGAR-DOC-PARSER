import os
import sys


import EDGAR


# Hyperparameters
tikr = 'nflx'
submission_date = '20210101' #Find nearest AFTER this date
headless = False

# Set up
loader = EDGAR.dataloader(data_dir='../data', api_keys_path='../api_keys.yaml');
loader.load_metadata(tikr)

# Get nearest 10Q form path to above date
dname = loader.get_nearest_date_filename(submission_date, tikr)
fname = loader.get_10q_name(dname, tikr)
driver_path = pathlib.Path(os.path.join(loader.proc_dir, tikr, dname, fname)).as_uri()

# Parsing
parser = EDGAR.parser(headless=headless)
found, annotation_dict = parser.parse_annotated_text(driver_path, highlight=True, save=False)

temp = input('Press Enter to close  Window')
