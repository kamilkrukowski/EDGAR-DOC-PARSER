class DocumentType:
    """
        Object for specifying type of document in download and parse functions.
    """

    RAW_FILE_DIR_NAME = '.rawcache'
    EXTRACTED_FILE_DIR_NAME = 'files'
    PARSED_FILE_DIR_NAME = 'parsed'
    META_FILE_DIR_NAME = '.metadata'

    # Currently implemented documents, and catcher for 'all'
    valid_types = {'all', '10q', '8k', 'other', 'ims'}

    def __init__(self, dtype='all', **kwargs):
        """
            Constructor

            Parameters:

            dtype: Union[str, DocumentType]
                The desired instance of DocumentType
        """
        if isinstance(dtype, str):
            self.dtype = DocumentType.parse_string(dtype)
            if self.dtype not in DocumentType.valid_types:
                raise RuntimeError('Invalid DocumentType Specified')
        elif isinstance(dtype, DocumentType):
            self.dtype = dtype.dtype

    def __contains__(self, item):
        """
            Returns whether a target is a DocumentType covered by this instance
            Notes:
            Intended for strings
        """
        if isinstance(item, str):
            item = item.lower().replace('-', '').strip()
            if item in self.valid_types:
                return True
        return False

    @staticmethod
    def parse_string(target):
        """
            Converts raw string to correct form for casting as DocumentClass
        """
        to_remove = {'-', ' ', 'form'}
        target = target.lower()
        for removeable in to_remove:
            target = target.replace(removeable, '')
        return target

    @staticmethod
    def is_valid_type(target):
        """
            Static method for checking whether a string can be cast as a type
        """
        if isinstance(target, DocumentType):
            return True
        if isinstance(target, str):
            return DocumentType.parse_string(
                target) in DocumentType.valid_types
        return False

    def __repr__(self):
        """
            Convert self to a string representation for console output
        """
        out = self.dtype
        if self.dtype in {'10q', '8k'}:
            return out[:-1] + '-' + out.upper()[-1]
        return out

    def __eq__(self, other):
        """
            Override for == with DocumentType and Str
        """
        return self.dtype == other
