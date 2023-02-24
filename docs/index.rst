.. pyEDGAR documentation master file, created by
   sphinx-quickstart on Fri Nov 18 16:56:37 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to EDGAR-DOC-PARSER's documentation!
===========================================

About
-------------------
A package for downloading, extracting, parsing, and processing data from SEC-EDGAR, a public online database of all documents filed with the USA's Securities and Exchange Commission.

Core Functionality
--------------------

Downloading and extracting archives of 10-Q submissions from the SEC API

.. code-block:: python

    import EDGAR

    tikr = 'nflx'
    data_dir = 'data'

    loader = EDGAR.downloader(data_dir=data_dir)
    metadata = EDGAR.metadata(data_dir=data_dir)

    # Load previous cached information
    metadata.load_tikr_metadata(tikr)

    loader.query_server(tikr)
    loader.unpack_bulk(tikr)

Parsing 10-Q submission HTML into featurized pandas DataFrames

.. code-block:: python

    parser = EDGAR.parser(data_dir=data_dir)

    metadata.load_tikr_metadata(tikr)
    annotated_docs = parser.get_annotated_submissions(tikr)

    document = annotated_docs[0]

    fname = metadata.get_10q_name(tikr, document)
    # Try load cached, otherwise regenerate new file
    features = parser.featurize_file(tikr, document, fname)


.. toctree::
   :maxdepth: 2

   setup
   core
   Downloading Documents <downloader>
   Parsing Documents <parser>
   Useful Metadata <metadata_mgr>
   DocumentType <document_type>



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
