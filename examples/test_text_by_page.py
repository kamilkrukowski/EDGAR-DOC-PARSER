"""
Should work on Netflix 2013 10-Q

Opens a local 'nflx' 10-Q form (or tries)
Extracts 'text' elements from HTM tree
Visualizes elements by red border highlighting in firefox browser
"""
import numpy as np


import sys; sys.path.append('..')
import os
import json


import EDGAR


# Hyperparameters
data_dir = os.path.join('..','data')
submission_date = "20210630"
tikr = 'nflx'
#EDGAR.set_data_dir(os.path.join('..','data'))

pipeline = EDGAR.preprocesser(data_dir=data_dir)

# Set up
loader = EDGAR.downloader(data_dir=data_dir)
loader.metadata.load_tikr_metadata(tikr)

parser = EDGAR.parser(data_dir=data_dir)

# Get nearest 10Q form path to above date
submission = loader.get_nearest_date_filename(tikr, submission_date)
filename = loader.metadata.get_10q_name(tikr, submission)
driver_path = parser.get_driver_path(tikr, submission, filename)


########### testing for parse_text_by_page ##################

def Test_parse_text_by_page(parser):
    # Serializing json
    text = parser.parse_text_by_page()
    # Writing to sample.json
    with open(os.path.join("..", "outputs", "sample.json"), "w") as outfile:
        json.dump(text, outfile, default=lambda o: '<not serializable>', sort_keys=True, indent=4)

########### testing for get_annotation_feature ##################
def Test_get_annotation_features(found, annotation_dict):
	parser.get_annotation_features(found, annotation_dict,save= True, out_path = os.path.join('..', 'outputs', 'sample.csv'))

found = None
if(int(submission_date) > 20200101):
  found, annotation_dict = parser._parse_annotated_text(driver_path, highlight=False, save=False)
  Test_get_annotation_features(found, annotation_dict)
else:
  found = parser._parse_unannotated_text(driver_path, highlight=False, save=True)
    
text_on = Test_parse_text_by_page(parser)