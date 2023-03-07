import re
import sys
from bs4 import BeautifulSoup
import tqdm

sys.path.append('src')
import EDGAR as edgar
import EDGAR.html as html
from EDGAR.subheader_parser_8k import Parser_8K 

DATA_DIR = '8kdata'

tikrs = ['aapl', 'msft', 'amzn', 'tsla', 'googl', 'goog',  'unh', 'jnj', 'cvx',
         'jpm', 'hd', 'v', 'pg']
metadata = edgar.Metadata(data_dir=DATA_DIR)
kparser = Parser_8K()

dataloader = edgar.DataLoader(tikrs=tikrs, document_type='8-K',
                              data_dir=DATA_DIR)
count_multi = 0
tikrs, submission,files, sections, texts, max_occurrence = [],[],[],[],[],[]

for idx, text in enumerate(dataloader):
    text_sec ,list_section = kparser.get_sections(text, True)

    filename = dataloader.files[idx]
    #submission, tikr are not easily available
    sub = dataloader.sub_lookup[filename]
    tikr = dataloader.tikr_lookup[sub]

    if(len(text_sec)  == 0 ):
        print(tikr, sub ,filename, 'no section')
        continue
    max_occur = 0
    # check max occurrence of the specified section
    for i, s in enumerate(list_section):
        curr_occur = kparser.get_num_occurrence(text, s)
        tikrs += [tikr]
        submission += [sub]
        files += [filename] 
        sections += [s]
        texts += [text_sec[i]]
        max_occurrence += [curr_occur]
        if curr_occur > max_occur:
            max_occur = curr_occur
    if max_occur > 1:
        count_multi += 1
print('number of files:',len(dataloader))
print("there are ", count_multi, "files has section name occur more than 1 time.")

with open("file.txt","w") as f:
    for (tikr, sub,file, section, t, occur) in zip(tikrs, submission,files, sections, texts, max_occurrence):
        f.write("{0},{1},{2},{3},{4},{5}\n".format(tikr, sub,file, section, t, occur))