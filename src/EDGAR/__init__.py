#!/usr/bin/env python # [1]
"""EDGAR Package."""
from .metadata_manager import metadata_manager as _Metadata
from .downloader import Downloader as _Downloader
from .parser import Parser as _Parser
from .document import DocumentType
from .wrappers import *
from . import pipeline

module_name = 'edgar'

_Downloader.__module__ = module_name
_Parser.__module__ = module_name
_Metadata.__module__ = module_name
DocumentType.__module__ = module_name

Metadata = pipeline.Metadata
Parser = pipeline.Parser
Downloader = pipeline.Downloader
