import os
import inspect

from .metadata_manager import metadata_manager as Metadata
from .downloader import Downloader
from .parser import Parser
from .document import DocumentType

DEFAULT_DATA_DIR = 'data'


class Pipeline:

    def __init__(self, data_dir: str = DEFAULT_DATA_DIR):

        self.data_dir = data_dir

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

    def load_files(self, tikrs: str, data_dir: str = DEFAULT_DATA_DIR,
                   document_type: str = '10q', force: bool = False,
                   remove_raw: bool = False, force_remove_raw: bool = False,
                   silent: bool = False):
        """
            Download local copies of document_type files 
                pertaining to a company

        Parameters
        ----------
        tikrs: str
            A list of companies to load dataframes for.
        force: bool
            if (True), then ignore locally downloaded files and
                overwrite them. Otherwise, attempt to detect
                previous download and abort server query.
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
        data_dir = self._relative_to_abs_path(data_dir)
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
