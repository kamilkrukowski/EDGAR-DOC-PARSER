"""HTML Parsing of Subheaders in HTML Documents."""
import re
from .document import DocumentType
from . import html


class Parser:
    """The base class from which all Parsers inherit, by DocumentType."""

    _document_type = None
    sections = None

    def __init__(self):
        """Initialize Base class."""
        
    def get_sections(self, htmltext: str) -> str:
        """Abstract method for extracting all sections from document."""
        raise NotImplementedError()

    def get_section(self, htmltext: str) -> str:
        """Abstract method for extracting section from document."""
        raise NotImplementedError()

    def section_exists(self, htmltext: str) -> bool:
        """Abstract method for verifying a section is in the document"""
        raise NotImplementedError()

    def __repr__(self) -> str:
        """Represent the class when cast as string."""
        return 'Parser Object'


class Parser_8K(Parser):
    """Extraction of content by header from 8-K Documents."""

    _document_type = DocumentType('8-K')

    # TODO ADD ALL SECTIONS, ADD ALL SECTION NAMES
    section_names = {"1.01": "entry into material agreement"}
    sections = {'1.01', '1.02'}

    def __init__(self):
        """Class constructor."""
        super().__init__()

    def clean_text(self, htmltext: str):
        """Clean the text before parsing"""

        # TODO ADD REMOVAL OF headers
        f = html.remove_tags(f)
        f = html.remove_htmlbytes(f)
        f = html.remove_newlines(f)
        f = html.remove_tabs(f)
        f = html.compress_spaces(f)
        f = f.lower()

    def get_sections(self, doctext: str, return_types: bool = False) -> list:
        """
        Extract all subsets of html corresponding to parsing sections.

        Parameters
        ----------
        htmltext: str
            The 8-K raw document to be searched
        return_types: bool = False
            if True, then returns a tuple (section_texts, section_headers)
        """

        doctext = self.clean_text()

        out = []
        _return_types = []
        for section in Parser_8K.sections:
            curr = self.get_section(doctext, section)
            if curr is not None:
                _return_types += section
                out += curr

        if return_types:
            return out, _return_types
        else:
            return out

    def get_section(self, doctext: str, section_type: str) -> str:
        """
        Extract subset of HTML string corresponding to specified section.

        Parameters
        ----------
        htmltext: str
            The 8-K raw document to be searched
        section_type: str
            One of '1.01','1.02','','','','' from Parser_8K.sections

        Notes
        -----
        If the section is not present, returns None
        """

        doctext = self.clean_text(doctext)

        # TODO add valid sections to list
        assert section_type in Parser_8K.sections, 'Invalid section selection'

        pattern = ''
        if section_type == Parser_8K.HEADER_ITEM_1_01:
            pattern = ''
        elif section_type == Parser_8K.HEADER_ITEM_1_02:
            pattern = ''

        if not self.section_exists(doctext, section_type):
            return None

        return re.match(pattern, doctext, flags=re.I)
    
    def section_exists(self, htmltext: str) -> bool:
        """Abstract method for verifying a section is in the document"""
        raise NotImplementedError()

    def __repr__(self):
        """Represent the class when cast as string."""
        return 'Parser (8-K) Object'
