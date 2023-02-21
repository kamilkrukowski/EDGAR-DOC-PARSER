"""
    Definitions of EDGAR package
"""
import warnings
import os
import inspect

from . import metadata_manager as Metadata
from .downloader import Downloader
from .parser import Parser
from .document import DocumentType

Downloader.__module__ = 'EDGAR'
Parser.__module__ = 'EDGAR'
Metadata.__module__ = 'EDGAR'
DocumentType.__module__ = 'EDGAR'


def _relative_to_abs_path(relative_p):
    if not os.path.isabs(relative_p):
        # stack[0] is this func, stack[1] is some EDGAR_singleton func
        # stack[2] should be caller of EDGAR_singleton func
        return os.path.abspath(
            os.path.join(
                inspect.stack()[2][1],
                os.pardir,
                relative_p))
    return relative_p


class EDGAR_singleton:

    def __init__(self):
        self.metadatas = None
        self.downloader = None
        self.parser = None

    def _get_metadata(self, reuse: bool = True, *args, **kwargs):
        kwargs['data_dir'] = _relative_to_abs_path(
            kwargs.get('data_dir', 'EDGAR_data'))

        if self.metadatas is None or not reuse:
            self.metadatas = {
                kwargs['data_dir']: _Metadata.metadata_manager(
                    *args, **kwargs)}
            if len(self.metadatas) > 1:
                warnings.warn(
                    'multiple data directories passed during initialization',
                    RuntimeWarning)
        return self.metadatas[kwargs['data_dir']]

    def _get_downloader(self, reuse: bool = True, *args, **kwargs):
        kwargs['data_dir'] = _relative_to_abs_path(
            kwargs.get('data_dir', 'EDGAR_data'))

        if 'metadata' not in kwargs:
            kwargs['metadata'] = self._get_metadata(
                data_dir=kwargs.get('data_dir', 'data'), reuse=reuse)
        if self.downloader is None or not reuse:
            self.downloader = _Downloader(*args, **kwargs)
        return self.downloader

    def _get_parser(self, reuse: bool = True, *args, **kwargs):
        kwargs['data_dir'] = _relative_to_abs_path(
            kwargs.get('data_dir', 'EDGAR_data'))

        if 'metadata' not in kwargs:
            kwargs['metadata'] = self._get_metadata(
                data_dir=kwargs.get('data_dir', 'data'), reuse=reuse)
        if self.parser is None or not reuse:
            self.parser = _Parser(*args, **kwargs)
        return self.parser


edgar_global = EDGAR_singleton()

_Metadata = edgar_global._get_metadata
_Downloader = edgar_global._get_downloader
_Parser = edgar_global._get_parser
