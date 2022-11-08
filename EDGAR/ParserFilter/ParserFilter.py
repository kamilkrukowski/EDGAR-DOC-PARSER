import re
import os

# determines if a file has annotation
class ParserFilter:
    # read the list of tags of annotation
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__),'tag_list.txt')) as f:
            self.tag_list = [line.rstrip() for line in f]
    # input: a opened file instance
    # output: whether the file is annotated
    def file_with_annotation(self, file):
        for tag in self.tag_list:
            if re.search(tag, file.read()):
                return True
        return False
