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

    def get_sections(self, doctext: str) -> str:
        """Abstract method for extracting all sections from document."""
        raise NotImplementedError()

    def get_section(self, doctext: str, section_type: str) -> str:
        """Abstract method for extracting section from document."""
        raise NotImplementedError()

    def section_exists(self, doctext: str, section_type: str) -> bool:
        """Abstract method for verifying a section is in the document."""
        raise NotImplementedError()

    def __repr__(self) -> str:
        """Represent the class when cast as string."""
        return 'Parser Object'


class Parser_8K(Parser):
    """Extraction of content by header from 8-K Documents."""

    _document_type = DocumentType('8-K')

    section_names = {
        '1.01': 'entry into a material definitive agreement',
        '1.02': 'termination of a material definitive agreement',
        '1.03': 'bankruptcy or receivership',
        '1.04': ('mine safety - reporting of shutdowns '
                 'and patterns of violations'),
        '2.01': 'acquisition or disposition of assets',
        '2.02': 'results of operations and financial condition',
        '2.03': ('creation of a direct financial obligation or an obligation '
                 'under an off-balance sheet arrangement of a registrant'),
        '2.04': ('triggering events that accelerate or increase a direct '
                 'financial obligation or an obligation under an off-balance '
                 'sheet arrangement'),
        '2.05': 'cost associated with exit or disposal activities',
        '2.06': 'material impairments',
        '3.01': ('notice of delisting or failure to satisfy a continued '
                 'listing rule or standard; transfer of listing'),
        '3.02': 'unregistered sales of equity securities',
        '3.03': 'material modifications to rights of security holders',
        '4.01': "changes in registrant's certifying accountant",
        '4.02': ('non-reliance on previously issued financial statements or '
                 'a related audit report or completed interim review'),
        '5.01': 'changes in control of registrant',
        '5.02': ('departure of directors or certain officers; election of '
                 'directors; appointment of certain officers; compensatory '
                 'arrangements of certain officers'),
        '5.03': ('amendments to articles of incorporation or bylaws; '
                 'change in fiscal year'),
        '5.04': ('temporary suspension of trading under registrant\'s '
                 'employee benefit plans'),
        '5.05': ('amendments to the registrant\'s code of ethics, or waiver '
                 'of a provision of the code of ethics'),
        '5.06': 'change in shell company status',
        '5.07': 'submission of matters to a vote of security holders',
        '5.08': 'shareholder director nominations',
        '6': "resignations of registrant's directors",
        '6.01': 'abs informational and computational material',
        '6.02': 'change of servicer or trustee',
        '6.03': 'change in credit enhancement or other external support',
        '6.04': 'failure to make a required distribution',
        '6.05': 'securities act updating disclosure',
        '7.01': 'regulation fd disclosure',
        '8.01': 'other events',
        '9.01': 'financial statements and exhibits'}

    sections = list(section_names.submissions())

    def __init__(self):
        """Class constructor."""
        super().__init__()

    def clean_text(self, doctext: str) -> str:
        """Clean the text before parsing."""
        f = html.remove_tags(doctext)
        f = html.remove_htmlbytes(f)
        f = html.remove_newlines(f)
        f = html.remove_tabs(f)
        f = html.compress_spaces(f)
        f = f.lower()

        return f

    def get_sections(self, doctext: str, return_types: bool = False,
                     keep_multi: bool = True) -> list:
        """
        Extract all subsets of html corresponding to parsing sections.

        Parameters
        ----------
        htmltext: str
            The 8-K raw document to be searched
        return_types: bool = False
            if True, then returns a tuple (section_texts, section_types)
        keep_multi: bool = True
            if False, only return section that has one occurrence.
        """
        doctext = self.clean_text(doctext)

        out = []
        _return_types = []
        for section in Parser_8K.sections:
            curr = self.get_section(doctext, section)
            if curr is not None:
                _return_types += [section]

                if not keep_multi and self._get_num_occurrence(
                                                doctext, section) > 1:
                    continue
                out += [curr]

        if return_types:
            return out, _return_types
        else:
            return out

    def _get_num_occurrence(self, doctext:  str, section_type: str) -> int:
        """
        Count the occurrence of the specified section in the HTML.

        Parameters
        ----------
        htmltext: str
            The 8-K raw document to be searched
        section_type: str
            Any target from Parser_8K.sections
        """
        doctext = self.clean_text(doctext)
        assert section_type in Parser_8K.sections, 'Invalid section selection'

        # check if section exist
        if not self.section_exists(doctext, section_type):
            return 0

        # create a pattern to search for section header
        pattern = f'{self.section_names[section_type]}'
        pattern = re.sub(' ', r'[ ]*', pattern)
        pattern = re.compile(pattern, re.IGNORECASE)

        return len(pattern.findall(doctext))

    def get_section(self, doctext: str, section_type: str) -> str:
        """
        Extract subset of HTML string corresponding to specified section.

        Parameters
        ----------
        htmltext: str
            The 8-K raw document to be searched
        section_type: str
            Choice from from Parser_8K.sections

        Notes
        -----
        If the section is not present, returns None
        """
        doctext = self.clean_text(doctext)

        assert section_type in Parser_8K.sections, 'Invalid section selection'

        # create a pattern to search for section header
        pattern = f'{self.section_names[section_type]}'
        pattern = re.sub(' ', r'[ ]*', pattern)

        # check if section exist
        if not self.section_exists(doctext, section_type):
            return None

        # find the start of the header
        pattern = re.compile(pattern, re.IGNORECASE)
        start_idx = re.search(pattern, doctext).end()  # , flags=re.I)

        end_pattern = re.compile(
            'item|Pursuant to the requirements', re.IGNORECASE)
        end_search = re.search(end_pattern, doctext[start_idx:])
        if end_search is not None:
            return doctext[start_idx:start_idx+end_search.start()]
        return doctext[start_idx:]

    def section_exists(self, doctext: str, section_type: str,
                       pattern: str = None) -> bool:
        """Verify a section is in the document."""
        assert section_type in Parser_8K.sections, 'Invalid section selection'
        # if no pattern input, then generate pattern
        if pattern is None:
            pattern = f'{self.section_names[section_type]}'
            pattern = re.sub(' ', r'[ ]*', pattern)
        pattern = re.compile(pattern, re.IGNORECASE)

        # Check if the section exists
        if len(pattern.findall(doctext)) > 0:
            return True
        return False

    def __repr__(self):
        """Represent the class when cast as string."""
        return 'Parser (8-K) Object'
