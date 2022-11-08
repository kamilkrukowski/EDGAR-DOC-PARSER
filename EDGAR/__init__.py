"""
    Definitions of EDGAR package
"""
from . import metadata_manager as edgar_metadata
from . import dataloader as edgar_dataloader
from . import parser as edgar_parser

dataloader = edgar_dataloader.edgar_dataloader
parser = edgar_parser.edgar_parser
Metadata = edgar_metadata.metadata_manager
