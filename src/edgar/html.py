#!/usr/bin/env python # [1]
"""Manipulate and clean html strings."""
import re

from bs4 import BeautifulSoup


def clean_text(text: str):
    """
    Remove all HTML tags and compress whitespace. \
    Removes improperly formatted tags.

    Notes
    -----
    Result is a string of words separated by single spaces.
    """
    if text is None:
        raise RuntimeError('text is None!')
    text = BeautifulSoup(text, features='lxml')

    # Get BeautifulSoup.body.text safely
    body = text.body
    if body is None:
        return ''
    text = body.text

    text = re.sub(' +', ' ', text.replace(
        ',', ' ').replace('\n', ' ').replace('\t', ' ')).strip()
    return re.sub('\xa0', '', text)


def remove_tags(htmltext: str) -> str:
    """Remove all HTML tags from text."""
    return re.sub(' +', ' ', htmltext.replace(
        ',', ' ').replace('\n', ' ').replace('\t', ' ')).strip()


def compress_spaces(text: str) -> str:
    """Replace multiple instances of spaces with one."""
    return re.sub(' +', ' ', text)


def split_pages(htmltext: str) -> list[str]:
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
