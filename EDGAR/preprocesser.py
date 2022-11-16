import os, pathlib


from .metadata_manager import metadata_manager
from .parser import edgar_parser as parser

class edgar_preprocesser:
    
    def __init__(self, data_dir, metadata = None, parser = None):

        self.data_dir = os.path.join(data_dir, '')

        # Always gets the path of the current file
        self.path = pathlib.Path().absolute()
        
        if metadata is None:
            self.metadata = metadata_manager(data_dir=data_dir);
        else:
            self.metadata = metadata

        if parser is None:
            self.parser = parser(self.data_dir, metadata = self.metadata) 
        else:
            self.parser = parser
        
    def preprocess_file(self, tikr: str, submission: str, filename: str, force: bool = False):
        features = self.parser.featurize_file(tikr, submission, filename, force=force)

        return features