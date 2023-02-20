

class DocumentType:
    
    RAW_FILE_DIR_NAME = '.rawcache'
    EXTRACTED_FILE_DIR_NAME = 'files'
    PARSED_FILE_DIR_NAME = 'parsed'
    META_FILE_DIR_NAME = '.metadata'

    # Currently implemented documents, and catcher for 'all'
    valid_types = {'all', '10q', '8k', 'other'}

    def __init__(self, *args, **kwargs):

        
        if len(args) == 0:
            self.dtype = 'all'
        elif type(args[0]) is str:
            self.dtype = DocumentType.parse_string(args[0])
            if self.dtype not in DocumentType.valid_types:
                raise RuntimeError("Invalid DocumentType Specified")
        elif type(args[0]) is DocumentType:
            self.dtype = args[0].dtype;
        

    def __contains__(self, item):
        if type(item) is str:
            item = item.lower().replace('-','').strip()
            if item in self.valid_types:
                return True;
        return False;

    @staticmethod
    def parse_string(target):
        to_remove = {'-', ' ', 'form'}
        target = target.lower()
        for removeable in to_remove:
            target = target.replace(removeable, '')
        return target

    @staticmethod
    def is_valid_type(target):
        if type(target) is DocumentType:
            return True
        if type(target) is str:
            return DocumentType.parse_string(target) in DocumentType.valid_types
        return False
        
    def __repr__(self):
        out = self.dtype
        if self.dtype in {'10q', '8k'}:
            return out[:-1] + '-' + out.upper()[-1]
        return out



    def __eq__(self, other):
        return self.dtype == other;

