from ParserFilter.ParserFilter import ParserFilter
import numpy as np
import os
P = ParserFilter()
path_nflx = os.path.join(os.path.dirname(__file__), 'edgar_downloads','processed','nflx')
has_annotation_list = []
# loop for each file
for filename in os.listdir(path_nflx):
    folder_path = os.path.join(path_nflx, filename)
    doc_list = os.listdir(folder_path)
    
    # the following loop filters out other documents
    ## my directory is contaminated by jupyter notebook checkpoint
    for i in doc_list:
        if i.endswith('htm'):
            doc = i
            break
            
    with open(os.path.join(folder_path, doc), encoding='utf-8') as f:
        has = bool(P.file_with_annotation(f))
    has_annotation_list += [[os.path.join(folder_path, doc[0]), has]]
    
# save the result
np.savetxt('file_has_annotation', np.array(has_annotation_list), '%s')
