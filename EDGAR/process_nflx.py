from dataloader import edgar_dataloader
import datetime
import time
loader = edgar_dataloader(data_dir='edgar_downloads')
tikrs = ['nflx']

max_num_filings = 3
start_date = datetime.datetime(2020, 1, 15)
end_date = datetime.datetime(2023, 7, 15)

# If we set all to None, we get everything
#    Metadata will note this and prevent re-pulling
max_num_filings = None
start_date = None
end_date = None

for tikr in tikrs:
    time.sleep(1)
    loader.metadata.load_tikr_metadata(tikr)

    print("First we download...")
    loader.query_server(tikr, start_date, end_date, max_num_filings)
    print("Look: if we try again it declines;")
    loader.query_server(tikr, start_date, end_date, max_num_filings)
    print("""Now we unpack all tikr filings in bulk locally
    but only for the 10-Q...""")
    loader.unpack_bulk(tikr, loading_bar=True)
    print("""We can also unpack individual files more thoroughly
            , i.e. for supporting figures.""")
    files = loader.get_unpackable_files(tikr)
    print(f"Here is one: {files[0]}")
    print("We are unpacking it...")
    loader.unpack_file(tikr, files[0], complete=False)
    print("All done!")
