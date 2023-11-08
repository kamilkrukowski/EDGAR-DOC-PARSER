.. edgar-doc-parser documentation master file, created by
   sphinx-quickstart on Fri Nov 18 16:56:37 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to EDGAR-DOC-PARSER's documentation!
============================================

About
-------------------
A package for downloading, extracting, parsing, and processing data from
SEC-EDGAR, a public online database of all documents filed with the USA's
Securities and Exchange Commission.

Core Functionality
--------------------

Dataloader for clean text from SEC forms

.. code-block:: python

    from edgar import DataLoader

    dataloader = DataLoader(tikrs=['nflx'], document_type='8-K',
                            data_dir='data')

    for text in dataloader:
        # Do Stuff
        pass

Downloading and extracting archives of supported submissions from the SEC API.

.. code-block:: python

    from edgar import load_files

    data_dir = 'data'
    tikr = 'nflx'
    tikrs = [tikrs]

    load_files(tikrs=tikrs, data_dir=data_dir, document_type='10-Q')


.. toctree::
   :maxdepth: 2

   setup
   core
   Dataloader <dataloader>
   Downloading Documents <downloader>
   Parsing Documents <parser>
   Useful Metadata <metadata>
   DocumentType <document_type>



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
