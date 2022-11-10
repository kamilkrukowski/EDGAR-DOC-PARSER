import datetime
import time
import sys; sys.path.append('../')


import EDGAR


loader = EDGAR.dataloader(data_dir=os.path.join('..', 'data'), api_keys_path = os.path.join('..', 'api_keys.yaml'))
tikrs = ['nflx']

for tikr in tikrs:
    time.sleep(1)
    loader.metadata.load_tikr_metadata(tikr)

    print("First we download...")
    loader.query_server(tikr, force=True)
    print("""Now we unpack all tikr filings in bulk locally
    but only for the 10-Q...""")
    loader.unpack_bulk(tikr, loading_bar=True, force=True)
    print("""We can also unpack individual files more thoroughly
            , i.e. for supporting figures.""")
    files = loader.get_unpackable_files(tikr)
    print(f"Here is one: {files[0]}")
    print("We are unpacking it...")
    loader.unpack_file(tikr, files[0], complete=False)
    print("All done!")
