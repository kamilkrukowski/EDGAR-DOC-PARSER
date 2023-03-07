"""
High level wrappers of functionality in common use cases
"""
import os
import pathlib
import inspect

from . import pipeline
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


def load_files(tikrs: str, data_dir: str = DEFAULT_DATA_DIR,
               document_type: str = '10-Q', force: bool = False,
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

    metadata = pipeline.singleton._get_metadata(data_dir=data_dir)
    loader = pipeline.singleton._get_downloader(data_dir=data_dir)
#    parser = edgar_global._get_parser(data_dir=data_dir)

    for tikr in tikrs:
        if force or not metadata.is_unpacked(tikr,
                                             document_type=document_type):
            if force or not metadata.is_downloaded(tikr):
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

    out_text = None
    with open(path, 'r', encoding = 'utf-8') as f:
        out_text = f.read()

    return out_text


def get_files(tikrs, submissions=None,
              data_dir: str = DEFAULT_DATA_DIR, metadata=None):
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
        metadata = pipeline.Metadata(data_dir=data_dir)
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
