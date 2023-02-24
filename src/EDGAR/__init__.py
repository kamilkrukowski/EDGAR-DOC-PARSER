"""
    Definitions of EDGAR package
"""
import os
import inspect

from .metadata_manager import metadata_manager as _Metadata
from .downloader import Downloader as _Downloader
from .parser import Parser as _Parser
from .document import DocumentType

_Downloader.__module__ = 'EDGAR'
_Parser.__module__ = 'EDGAR'
_Metadata.__module__ = 'EDGAR'
DocumentType.__module__ = 'EDGAR'

__version__ = '0.0.5'

DEFAULT_DATA_DIR = 'edgar_data'


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


class Pipeline:

    def __init__(self, data_dir=DEFAULT_DATA_DIR):
        self.metadata = None
        self.downloader = None
        self.parser = None

        self.data_dir = data_dir

    def _get_metadata(self, data_dir: str = DEFAULT_DATA_DIR,
                      reuse: bool = True, *args, **kwargs):
        """
        Loads a metadata associated with the desired data_dir

        Parameters
        ----------
        data_dir: str = \'edgar_data\'
            The location to store loaded data and search for metadata
        reuse: bool, Optional
            If False, re-initializes the class if an instance already exists
        """
        kwargs['data_dir'] = _relative_to_abs_path(data_dir)
        if self.metadata is None or not reuse:
            self.metadata = _Metadata(*args, **kwargs)
        return self.metadata

    def _get_downloader(self, data_dir: str = DEFAULT_DATA_DIR,
                        reuse: bool = True, **kwargs):
        """
        Loads a Downloader associated with the desired data_dir

        Parameters
        ----------
        data_dir: str = \'edgar_data\'
            The location to store loaded data and search for metadata
        reuse: bool, Optional
            If False, re-initializes the class if an instance already exists
        """
        kwargs['data_dir'] = _relative_to_abs_path(data_dir)

        if 'metadata' not in kwargs:
            kwargs['metadata'] = self._get_metadata(
                data_dir=data_dir, reuse=reuse)
        if self.downloader is None or not reuse:
            self.downloader = _Downloader(**kwargs)
        return self.downloader

    def _get_parser(self, data_dir: str = DEFAULT_DATA_DIR,
                    reuse: bool = True, **kwargs):
        """
        Loads a Parser associated with the desired data_dir

        Parameters
        ----------
        data_dir: str = \'edgar_data\'
            The location to store loaded data and search for metadata
        reuse: bool, Optional
            If False, re-initializes the class if an instance already exists
        """
        kwargs['data_dir'] = _relative_to_abs_path(data_dir)

        if 'metadata' not in kwargs:
            kwargs['metadata'] = self._get_metadata(
                data_dir=kwargs.get('data_dir', 'data'), reuse=reuse)
        if self.parser is None or not reuse:
            self.parser = _Parser(**kwargs)
        return self.parser


class EDGAR_singleton:

    def __init__(self):
        self.pipelines = None

    def _get_metadata(self, data_dir: str = DEFAULT_DATA_DIR,
                      reuse: bool = True, **kwargs):
        """
        Loads a metadata associated with the desired data_dir

        Parameters
        ----------
        data_dir: str = \'edgar_data\'
            The location to store loaded data and search for metadata
        reuse: bool, Optional
            If False, re-initializes the class if an instance already exists
        """
        data_dir = _relative_to_abs_path(data_dir)

        if self.pipelines is None:
            self.pipelines = {
                data_dir: Pipeline(data_dir=data_dir,  **kwargs)}
        return self.pipelines[data_dir]._get_metadata(
            data_dir=data_dir, reuse=reuse, **kwargs)

    def _get_downloader(self, data_dir: str = DEFAULT_DATA_DIR,
                        reuse: bool = True, *args, **kwargs):
        """
        Loads a Downloader associated with the desired data_dir

        Parameters
        ----------
        data_dir: str = \'edgar_data\'
            The location to store loaded data and search for metadata
        reuse: bool, Optional
            If False, re-initializes the class if an instance already exists
        """
        data_dir = _relative_to_abs_path(data_dir)

        if self.pipelines is None:
            self.pipelines = {
                data_dir: Pipeline(data_dir=data_dir,  **kwargs)}
        return self.pipelines[data_dir]._get_downloader(
            data_dir=data_dir, reuse=reuse, **kwargs)

    def _get_parser(self, data_dir: str = DEFAULT_DATA_DIR,
                    reuse: bool = True, *args, **kwargs):
        """
        Loads a Parser associated with the desired data_dir

        Parameters
        ----------
        data_dir: str = \'edgar_data\'
            The location to store loaded data and search for metadata
        reuse: bool, Optional
            If False, re-initializes the class if an instance already exists
        """
        data_dir = _relative_to_abs_path(data_dir)

        if self.pipelines is None:
            self.pipelines = {
                data_dir: Pipeline(data_dir=data_dir,  **kwargs)}
        return self.pipelines[data_dir]._get_parser(
            data_dir=data_dir, reuse=reuse, **kwargs)


def load_files(tikrs: str, data_dir: str = DEFAULT_DATA_DIR,
               document_type: str = '10q', force: bool = False,
               remove_raw: bool = False, force_remove_raw: bool = False,
               silent: bool = False):
    """
        Download local copies of document_type files pertaining to a company

    Parameters
    ----------
    tikrs: str
        A list of companies to load dataframes for.
    force: bool
        if (True), then ignore locally downloaded files and
            overwrite them. Otherwise, attempt to detect
            previous download and abort server query.
    loading_bar: bool
        if True, will time and show progress
    document_type: str or DocumentType
        The type of filings in question
    remove_raw: bool, Optional
        If True, will delete each raw file after it is extracted
    force_remove_raw: bool, Optional
        If True, will delete all files in the unpacking directory
        even if some are not unpacked.
    silent: bool, Optional
        If True, will silence all warnings
    """
    data_dir = _relative_to_abs_path(data_dir)
    if type(tikrs) is str:
        tikrs = [tikrs]
    assert type(tikrs) is list

    metadata = edgar_global._get_metadata(data_dir=data_dir)
    loader = edgar_global._get_downloader(data_dir=data_dir)
#    parser = edgar_global._get_parser(data_dir=data_dir)

    for tikr in tikrs:
        if not metadata.is_unpacked(tikr, document_type=document_type):
            if not metadata.is_downloaded(tikr):
                loader.query_server(tikr, force=force,
                                    document_type=document_type,
                                    silent=silent)

            loader.unpack_bulk(
                tikr,
                force=force,
                document_type=document_type,
                desc=f'{tikr} :Inflating HTM',
                remove_raw=remove_raw,
                force_remove_raw=force_remove_raw,
                silent=silent)

    """
        annotated_docs = parser.get_annotated_submissions(tikr, silent=True)

        # to process the documents and extract relevant information.
        for doc in annotated_docs:
            fname = metadata.get_10q_name(tikr, doc)
            features = parser.featurize_file(
                tikr, doc, fname, force=force, silent=True, clean_raw=False)
            if features is not None:
                pass
    """


edgar_global = EDGAR_singleton()

Metadata = edgar_global._get_metadata
Downloader = edgar_global._get_downloader
Parser = edgar_global._get_parser
