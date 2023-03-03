"""HTML Parsing of Subheaders in HTML Documents."""
import re
from .document import DocumentType


class Parser:
    """The base class from which all Parsers inherit, by DocumentType."""

    _document_type = None
    sections = None

    def __init__(self):
        """Initialize Base class."""

    def get_section(self, htmltext: str):
        """Abstract method for extracting section from document."""
        raise NotImplementedError()

    def __repr__(self):
        """Represent the class when cast as string."""
        return 'Parser Object'


class Parser_8K(Parser):
    """Extraction of content by header from 8-K Documents."""

    _document_type = DocumentType('8-K')

    HEADER_ITEM_1_01 = ''
    HEADER_ITEM_1_02 = ''

    sections = {HEADER_ITEM_1_01, HEADER_ITEM_1_02}

    def __init__(self):
        """Class constructor."""
        super().__init__()

    def get_section(self, doctext: str, section_type: str):
        """
        Extract subset of HTML string corresponding to specified section.

        Parameters
        ----------
        htmltext: str
            The 8-K raw document to be searched
        section_type: str
            One of '','','','','','' from Parser_8K.sections
        """
        # TODO add valid sections to list
        assert section_type in Parser_8K.sections, 'Invalid section selection'

        pattern = ''
        if section_type == Parser_8K.HEADER_ITEM_1_01:
            pattern = ''
        elif section_type == Parser_8K.HEADER_ITEM_1_02:
            pattern = ''

        return re.match(pattern, doctext, flags=re.I)

    def __repr__(self):
        """Represent the class when cast as string."""
        return 'Parser (8-K) Object'
