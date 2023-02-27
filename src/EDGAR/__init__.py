#!/usr/bin/env python # [1]
"""EDGAR Package."""
import os
import inspect
import pathlib

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
    """Group a set of metadata, parser, downloader associated with one \
        DATA_DIR."""

    def __init__(self, data_dir=DEFAULT_DATA_DIR):
        """Keep track of module instances under desired DATA_DIR."""
        self.metadata = None
        self.downloader = None
        self.parser = None

        self.data_dir = data_dir

    def _get_metadata(self, data_dir: str = DEFAULT_DATA_DIR,
                      reuse: bool = True, *args, **kwargs):
        """
        Load a metadata associated with the desired data_dir.

        Parameters
        ----------
        data_dir: str
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
        Load a Downloader associated with the desired data_dir.

        Parameters
        ----------
        data_dir: str
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
        Load a Parser associated with the desired data_dir.

        Parameters
        ----------
        data_dir: str
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
    """
    Intercept constructors for module classes and attempt to force re-use of\
    existing instances.

    Notes
    -----
    The existance of multiple Metadata classes can cause desync of updates
    across the metadata. The global singleton intercept this creation and
    discourages the creation of multiple instances.
    """

    def __init__(self):
        """Keep track of separate data_dir constructors."""
        self.pipelines = {}

    def _get_metadata(self, data_dir: str = DEFAULT_DATA_DIR,
                      reuse: bool = True, **kwargs):
        """
        Load a metadata associated with the desired data_dir.

        Parameters
        ----------
        data_dir: str
            The location to store loaded data and search for metadata
        reuse: bool, Optional
            If False, re-initializes the class if an instance already exists
        """
        data_dir = _relative_to_abs_path(data_dir)

        if data_dir not in self.pipelines:
            self.pipelines[data_dir] = Pipeline(data_dir=data_dir,  **kwargs)
        return self.pipelines[data_dir]._get_metadata(
            data_dir=data_dir, reuse=reuse, **kwargs)

    def _get_downloader(self, data_dir: str = DEFAULT_DATA_DIR,
                        reuse: bool = True, *args, **kwargs):
        """
        Load a Downloader associated with the desired data_dir.

        Parameters
        ----------
        data_dir: str
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
        Load a Parser associated with the desired data_dir.

        Parameters
        ----------
        data_dir: str
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
               silent: bool = False, include_supplementary: bool = False):
    """
    Download local copies of document_type files pertaining to a company.

    Parameters
    ----------
    tikrs: str
        A list of companies to load dataframes for.
    force: bool = False
        if (True), then ignore locally downloaded files and
        overwrite them. Otherwise, attempt to detect
        previous download and abort server query.
    document_type: str or DocumentType
        The type of filings in question
    include_supplementary: bool = False
        If (True), then load all supplementary material as well.
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
                silent=silent,
                include_supplementary=include_supplementary)


def read_file(tikr: str, submission: str, file: str = None,
              document_type: str = '10-Q', data_dir=DEFAULT_DATA_DIR):
    """
    Load the contents of a file in a company filing submission.

    Parameters
    ----------
    tikr: str
        A companies to load the file for
    submission: str
        The filing to load the file from
    file: str, Optional
        If not specified, will attempt to load the primary file and ignore
        supplementary information
    data_dir: str
        The directory that filings are stored in
    """
    document_type = DocumentType(document_type)
    submission = submission.split('.')[0]
    if file is None:
        raise NotImplementedError()
    path = pathlib.Path(os.path.join(data_dir,
                                     DocumentType.EXTRACTED_FILE_DIR_NAME,
                                     tikr,
                                     document_type.dtype,
                                     submission,
                                     file)).absolute()

    if not os.path.exists(path):
        raise FileNotFoundError(f'{path}')
    return open(path, 'r').read()


def get_files(tikrs: list[str], submissions: list[str] = None,
              data_dir: str = DEFAULT_DATA_DIR, metadata=None) -> list[str]:
    """
    Get a list of all the locally loaded files under a company or specific\
    submission.

    Parameters
    ----------
    tikrs: list[str] or str
        The companies to get file lists for
    submissions: list[str] or None
        if None, return all possible file targets, otherwise only return
        files under the submissions in the list
    """
    if metadata is None:
        metadata = Metadata(data_dir=data_dir)
    if type(tikrs) is str:
        tikrs = [tikrs]

    if type(submissions) is str:
        submissions = [submissions]
    if submissions is not None:
        submissions = set(submissions)

    out = []
    for tikr in tikrs:
        for submission in metadata.get_submissions(tikr):

            # Sentinel for skip this one
            if submissions is not None:
                if submission not in submissions:
                    continue

            sub = metadata._get_submission(tikr, submission)['documents']
            for file in sub:
                out.append(sub[file]['filename'])
    return out


edgar_global = EDGAR_singleton()

Metadata = edgar_global._get_metadata
Downloader = edgar_global._get_downloader
Parser = edgar_global._get_parser
