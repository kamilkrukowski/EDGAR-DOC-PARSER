"""
    Definitions of EDGAR package
"""
import warnings

from . import metadata_manager as edgar_metadata
from . import downloader as edgar_downloader
from . import parser as edgar_parser


class EDGAR_singleton:
    
    def __init__(self):
        self.metadatas = {}
        self.downloader = None
        self.parser = None

    
    def _get_metadata(self,reuse: bool = True, *args, **kwargs):
        if self.metadata is None or not reuse:
            self.metadata = edgar_metadata.metadata_manager(*args, **kwargs)
            self.metadatas[self.metadata.data_dir] = self.metadata
            if len(self.metadatas) > 1:
                warnings.warn("multiple data directories passed during initialization", RuntimeWarning)
        return self.metadatas[kwargs['data_dir']]
    
    def _get_downloader(self,reuse: bool = True, *args, **kwargs):
        if 'metadata' not in kwargs:
            kwargs['metadata'] = self._get_metadata(data_dir=kwargs.get('data_dir', 'data'), reuse=reuse)
        if self.downloader is None or not reuse:
            self.downloader = edgar_downloader.edgar_downloader(*args, **kwargs)
        return self.downloader
 
    def _get_parser(self,reuse: bool = True, *args, **kwargs):
        if 'metadata' not in kwargs:
            kwargs['metadata'] = self._get_metadata(data_dir=kwargs.get('data_dir', 'data'), reuse=reuse)
        if self.parser is None or not reuse:
            self.parser = edgar_parser.edgar_parser(*args, **kwargs)
        return self.parser 


edgar_global = EDGAR_singleton()

metadata = edgar_global._get_metadata
downloader = edgar_global._get_downloader
parser = edgar_global._get_parser
