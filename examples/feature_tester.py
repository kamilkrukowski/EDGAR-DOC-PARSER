import os
import sys; sys.path.append('..')


import EDGAR


data_dir = os.path.join('..','data')
submission_date = "20210101"
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

features = pipeline.preprocess_file(tikr, submission, filename)
f = features