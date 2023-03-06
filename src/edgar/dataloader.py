"""Iterable string dataloaders for contents of SEC submissions."""
import os
import inspect
from typing import Callable


from tqdm.auto import tqdm


from .wrappers import load_files, get_files, read_file
from .document import DocumentType
from .pipeline import Metadata
from .html import clean_text


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


class DataLoader:
    """Master class for iterating through parsed text of filing submissions."""

    def __init__(self, tikrs: str, document_type: str,
                 data_dir: str = DocumentType.DEFAULT_DATA_DIR,
                 force_remove_raw: bool = False,
                 parser: Callable[[str], str] = clean_text,
                 loading_bar: bool = True):
        """
        Construct desired dataloading pipeline.

        Parameters
        ----------
        tikrs: List[str]
            A set of companies to load documents for.
        document_type: DocumentType or str
            The submission type to load documents for.
        parser: Callable[[str], str]
            A function that turns a raw document into cleaned output.
        loading_bar: bool = True
            if True, will display a tqdm loading bar while downloading files.

        Notes
        -----
        If files for associated company tickers are not available locally,
        will download and cache them during initialization for future use.
        """
        super().__init__()

        self.DATA_DIR = _relative_to_abs_path(data_dir)
        self.metadata = Metadata(data_dir=self.DATA_DIR)
        self.clean_func = parser

        if type(tikrs) is str:
            tikrs = [tikrs]

        self.document_type = DocumentType(document_type)

        self.files = []
        self.sub_lookup = {}
        self.tikr_lookup = {}

        itera = tikrs
        if loading_bar:
            itera = tqdm(tikrs, desc='Loading Files', leave=False)

        for tikr in itera:
            load_files(tikr, data_dir=self.DATA_DIR,
                       document_type=self.document_type,
                       include_supplementary=False,
                       force_remove_raw=force_remove_raw)

        submissions = self.metadata.get_submissions(tikr)
        for sub in submissions:
            files = get_files(tikrs=tikr, submissions=sub,
                              metadata=self.metadata)
            for file in files:
                if self.metadata._get_file(tikr, sub,
                                           file).get('extracted', False):
                    self.files.append(file)
                    self.sub_lookup[file] = sub
                    self.tikr_lookup[sub] = tikr

        self.idx = 0
        self.end = len(self) - 1

    def __iter__(self):
        """Generate iterable from class."""
        return self

    def __len__(self):
        """Get the number of files that can be loaded."""
        return len(self.files)

    def __next__(self):
        """When used as iterable, get the next item in index."""
        if self.idx > self.end:
            raise StopIteration
        else:
            self.idx += 1
            return self.__getitem__(self.idx - 1)

    def __getitem__(self, arg: int):
        """Load and clean the file associated with index idx."""
        if isinstance(arg, int):
            return self.__load_idx(arg)
        elif isinstance(arg, slice):
            # Get the start, stop, and step from the slice
            start = 0 if arg.start is None else arg.start
            stop = arg.stop
            step = 1 if arg.step is None else arg.step
            return [self.__load_idx(i) for i in range(start, stop, step)]
        else:
            raise RuntimeError('Improper indexing')

    def __load_idx(self, idx: int):
        file = self.files[idx]
        sub = self.sub_lookup[file]
        tikr = self.tikr_lookup[sub]
        f = read_file(tikr, sub, file, document_type=self.document_type,
                      data_dir=self.DATA_DIR)
        return self.clean_func(f)

    def __setitem__(self, idx: int):
        """Warn users if they attempt unsupported behaviour."""
        raise RuntimeError('Cannot set elements of File Loader')
