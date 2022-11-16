"""
    Definitions of EDGAR package
"""
from . import metadata_manager as edgar_metadata
from . import dataloader as edgar_dataloader
from . import downloader as edgar_downloader
from . import preprocesser as edgar_preprocesser
from . import parser as edgar_parser


class EDGAR_singleton:
    
    def __init__(self):
        self.metadata = None
        self.downloader = None
        self.parser = None
        self.dataloader = None
        self.preprocesser = None
    
    def _get_metadata(self, reuse: bool = False, *args, **kwargs):
        if self.metadata is None or not reuse:
            self.metadata = edgar_metadata.metadata_manager(*args, **kwargs)
        return self.metadata
    
    def _get_downloader(self, reuse: bool = False, *args, **kwargs):
        if 'metadata' not in kwargs:
            kwargs['metadata'] = self._get_metadata(data_dir=kwargs['data_dir'], reuse=reuse)
        if self.downloader is None or not reuse:
            self.downloader = edgar_downloader.edgar_downloader(*args, **kwargs)
        return self.downloader
 
    def _get_parser(self, reuse: bool = False, *args, **kwargs):
        if 'metadata' not in kwargs:
            kwargs['metadata'] = self._get_metadata(data_dir=kwargs['data_dir'], reuse=reuse)
        if self.parser is None or not reuse:
            self.parser = edgar_parser.edgar_parser(*args, **kwargs)
        return self.parser 
    
    def _get_dataloader(self, reuse: bool = False, *args, **kwargs):
        if 'metadata' not in kwargs:
            kwargs['metadata'] = self._get_metadata(data_dir=kwargs['data_dir'], reuse=reuse)
        if self.dataloader is None or not reuse:
            self.dataloader = edgar_dataloader.EDGARDataset(*args, **kwargs)
        return self.dataloader
    
    def _get_preprocesser(self, reuse: bool = False, *args, **kwargs):
        if 'metadata' not in kwargs:
            kwargs['metadata'] = self._get_metadata(data_dir=kwargs['data_dir'], reuse=reuse)
        if 'parser' not in kwargs:
            kwargs['parser'] = self._get_parser(data_dir=kwargs['data_dir'], reuse=reuse)
        if self.preprocesser is None or not reuse:
            self.preprocesser = edgar_preprocesser.edgar_preprocesser(*args, **kwargs)
        return self.preprocesser 
    

edgar_global = EDGAR_singleton()

metadata = edgar_global._get_metadata
downloader = edgar_global._get_downloader
parser = edgar_global._get_parser
preprocesser = edgar_global._get_preprocesser
dataloader = edgar_global._get_dataloader
