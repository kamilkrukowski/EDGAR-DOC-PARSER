.. _core:

Core Functionality
==================

The core loop for downloading and extract archives of 10-Q submission is as follows:

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

The result is html document files. These can be parsed into text fields and annotations Pandas Dataframe using the core loop:

.. code-block:: python

    parser = EDGAR.parser(data_dir=data_dir)

    metadata.load_tikr_metadata(tikr)
    annotated_docs = parser.get_annotated_submissions(tikr)

    document = annotated_docs[0]
    
    fname = metadata.get_10q_name(tikr, document)
    # Try load cached, otherwise regenerate new file
    features = parser.featurize_file(tikr, document, fname) 



Core Functions
---------------

.. automethod:: EDGAR.parser.edgar_parser.featurize_file 
    :noindex:

.. automethod:: EDGAR.downloader.edgar_downloader.query_server
    :noindex:

.. automethod:: EDGAR.downloader.edgar_downloader.unpack_bulk
    :noindex: