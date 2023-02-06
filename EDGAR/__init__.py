"""
    Definitions of EDGAR package
"""
from . import metadata_manager as edgar_metadata
from . import downloader as edgar_downloader
from . import preprocesser as edgar_preprocesser
from . import parser as edgar_parser
from . import data_subset as edgar_subset


class EDGAR_singleton:
    
    def __init__(self):
        self.metadata = None
        self.downloader = None
        self.parser = None
        self.preprocesser = None
        self.edgar_subset = None
    
    def _get_metadata(self,reuse: bool = True, *args, **kwargs):
        if self.metadata is None or not reuse:
            self.metadata = edgar_metadata.metadata_manager(*args, **kwargs)
        return self.metadata
    
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
    
    def _get_preprocesser(self,reuse: bool = True, *args, **kwargs):
        if 'metadata' not in kwargs:
            kwargs['metadata'] = self._get_metadata(data_dir=kwargs.get('data_dir', 'data'), reuse=reuse)
        if 'parser' not in kwargs:
            kwargs['parser'] = self._get_parser(data_dir=kwargs.get('data_dir', 'data'), reuse=reuse)
        if self.preprocesser is None or not reuse:
            self.preprocesser = edgar_preprocesser.edgar_preprocesser(*args, **kwargs)
        return self.preprocesser

    def _get_subset(self,reuse: bool = True, *args, **kwargs):
        if 'metadata' not in kwargs:
            kwargs['metadata'] = self._get_metadata(data_dir=kwargs.get('data_dir', 'data'), reuse=reuse)
        if 'parser' not in kwargs:
            kwargs['parser'] = self._get_parser(data_dir=kwargs.get('data_dir', 'data'), reuse=reuse)
        if self.edgar_subset is None or not reuse:
            self.edgar_subset = edgar_subset.DataSubset(*args, **kwargs)
        return self.edgar_subset
    

edgar_global = EDGAR_singleton()

metadata = edgar_global._get_metadata
downloader = edgar_global._get_downloader
parser = edgar_global._get_parser
preprocesser = edgar_global._get_preprocesser
subset = edgar_global._get_subset
