#!/usr/bin/env python # [1]
from .metadata_manager import metadata_manager as _Metadata
from .downloader import Downloader as _Downloader
from .parser import Parser as _Parser
from .document import DocumentType
from .wrappers import load_files, get_files, read_file
from . import pipeline
from .dataloader import DataLoader

module_name = 'edgar'

_Downloader.__module__ = module_name
_Parser.__module__ = module_name
_Metadata.__module__ = module_name
DocumentType.__module__ = module_name
DataLoader.__module__ = module_name

_, _, _ = load_files, get_files, read_file

Metadata = pipeline.Metadata
Parser = pipeline.Parser
Downloader = pipeline.Downloader
