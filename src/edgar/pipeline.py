"""
Group together processing elements into shared object with synchronized
metadata. Prevent desync of using multiple metadata objects by intercepting
constructors for processing elements and re-using metadata instances.
"""
import os
import inspect

from .metadata_manager import metadata_manager as _Metadata
from .downloader import Downloader as _Downloader
from .parser import Parser as _Parser
from .document import DocumentType


DEFAULT_DATA_DIR = DocumentType.DEFAULT_DATA_DIR


def _relative_to_abs_path(relative_p):
    """
    Find the path to the module calling the caller of this function.

    Notes:
    Stack looks like this: (_relative_to_abs_path, caller, caller's caller)
    This function returns the absolute path to the caller's caller.
    """
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

        if data_dir not in self.pipelines:
            self.pipelines[data_dir] = Pipeline(data_dir=data_dir,  **kwargs)
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

        if data_dir not in self.pipelines:
            self.pipelines[data_dir] = Pipeline(data_dir=data_dir,  **kwargs)
        return self.pipelines[data_dir]._get_parser(
            data_dir=data_dir, reuse=reuse, **kwargs)


singleton = EDGAR_singleton()

Metadata = singleton._get_metadata
Downloader = singleton._get_downloader
Parser = singleton._get_parser
