.. _downloader:

Downloading Files
=================

API User-Agent Fields
---------------------

The SEC requires all EDGAR users to identify themselves.
When the ``Downloader`` is used for the first time, it will prompt the user for API key information then cache it and re-use it in future iterations.

In order to edit these values after initialization, visit ``.keys.yaml`` in an associated data_directory.

Downloader Class
----------------------
.. autoclass:: edgar.Downloader
    :members:
