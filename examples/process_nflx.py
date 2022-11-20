import time
import os
import sys; sys.path.append('..')
import argparse

import EDGAR


# Command line magic for common use case to regenerate dataset
#   --force to overwrite outdated local files
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--force', action='store_true')
args = parser.parse_args()


loader = EDGAR.downloader(data_dir=os.path.join('..', 'data'))
tikrs = ['nflx']

for tikr in tikrs:
    time.sleep(1)
    loader.metadata.load_tikr_metadata(tikr)

    print("First we download...")
    loader.query_server(tikr, force=args.force)
    print("""Now we unpack all tikr filings in bulk locally
    but only for the 10-Q...""")
    loader.unpack_bulk(tikr, loading_bar=True, force=args.force)
    print("""We can also unpack individual files more thoroughly
            , i.e. for supporting figures.""")
    files = loader.get_unpackable_files(tikr)
    print(f"Here is one: {files[0]}")
    print("We are unpacking it...")
    loader.unpack_file(tikr, files[0], complete=False)
    print("All done!")
