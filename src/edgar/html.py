#!/usr/bin/env python # [1]
"""Manipulate and clean html strings."""
import re
from typing import List


def clean_text(text: str):
    """
    Remove all HTML tags and compress whitespace. \
    Removes improperly formatted tags.

    Notes
    -----
    Result is a string of words separated by single spaces.
    """
    text = remove_tags(text)  # Remove html <> tags
    text = remove_htmlbytes(text)
    text = re.sub('[\n\t]', ' ', text)  # Remove newlines / tabs
    text = compress_spaces(text)
    return text


def remove_fileheader(htmltext: str):
    """Remove the <document> <sequence> <description> tags from html doc."""
    raise NotImplementedError()


def remove_htmlbytes(text: str):
    """Remove formatted bytes from html strings."""
    text = re.sub('[(\xa0)(\x91)(\x92)(\x93)(\x94)]', ' ', text)
    return text


def remove_tags(htmltext: str) -> str:
    """Remove all HTML tags from text."""
    return re.sub('<.*?>', ' ', htmltext, flags=re.DOTALL)


def compress_spaces(text: str) -> str:
    """Replace multiple instances of spaces with one."""
    return re.sub(' +', ' ', text)


def remove_newlines(text: str) -> str:
    r"""Replace newlines with \' \'."""
    return re.sub('\n', ' ', text)


def remove_tabs(text: str) -> str:
    r"""Replace \t with \' \'."""
    return re.sub('\t', ' ', text)


def split_pages(htmltext: str) -> List[str]:
    """
    Return html text split along pagebreaks. Keeps some HTML tags.

    Notes
    -----
    Result is not guaranteed to close all tags properly, but works properly
    with clean_text
    """
    return re.split("<[^>]+ style=\"page-break-after:[ ]*always\"[^>]*>",
                    htmltext, flags=re.I)


def remove_tables(htlmtext: str) -> str:
    """Delete all <table></table> entries in html."""
    return re.sub('<table(.|\n)*?</table>', '', string=htlmtext, flags=re.I)
