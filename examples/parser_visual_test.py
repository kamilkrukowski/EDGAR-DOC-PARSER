"""
Opens a local 'nflx' 10-Q form (or tries)
Extracts 'text' elements from HTM tree
Visualizes elements by red border highlighting in firefox browser
"""
import pandas as pd
import numpy as np


import os
import pathlib
import sys ; sys.path.append('..')


import EDGAR


# Hyperparameters
tikr = 'nflx'
submission_date = '20210101' #Find nearest AFTER this date
headless = False

# Set up
loader = EDGAR.downloader(data_dir=os.path.join('..','data'));
loader.metadata.load_tikr_metadata(tikr)

# Get nearest 10Q form path to above date
dname = loader.get_nearest_date_filename(tikr, submission_date)
fname = loader.metadata.get_10q_name(tikr, dname)
driver_path = pathlib.Path(os.path.join(loader.proc_dir, tikr, dname, fname)).as_uri()

parser = EDGAR.parser(metadata=loader.metadata, headless=headless)

# Parsing
data = None

found, annotation_dict, in_table = parser._parse_annotated_text(driver_path, highlight=True, save=False)
parser.get_annotation_features(found, annotation_dict, in_table, save = True)
#input("enter to continue")

print(f'Saving sample data to \'outputs/sample_data.txt\'')
if not os.path.exists(os.path.join('..','outputs')):
    os.system('mkdir -p '+os.path.join('..','outputs'))
with open(os.path.join('..', 'outputs', 'sample_data.txt'), 'w') as f:
    for i in data:
        f.write(i[0]['value'])
        f.write('\t')
        f.write(i[1][0]['name'])
        for j in i[1][1:]:
            f.write(',')
            f.write(j['name'])
        f.write('\n')
