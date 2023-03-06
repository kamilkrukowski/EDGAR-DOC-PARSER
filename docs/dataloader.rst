.. _dataloader:

DataLoader Class
----------------------
.. autoclass:: edgar.DataLoader
    :members:

    .. automethod:: __init__

Usage
=====
The DataLoader will find, load, and return parsed text from a set of desired
documents. The constructor downloads the necessary files and the text is
extracted just-in-time when the user calls for it.

The interface supports slice-indexing and iterating.

.. code-block:: python
    :linenos:

    from edgar import DataLoader

    data = DataLoader(tikrs=['nflx'], '8-K')

.. code-block:: python
    :linenos:
    :lineno-start: 4

    print(data[14])

.. code-block:: python
    :linenos:
    :lineno-start: 5

    for text in data:
        print(text)

.. code-block:: python
    :linenos:
    :lineno-start: 7

    print(data[:3])

Custom Parse Functions
========================

In order to access raw data, we can pass in 'no operation' cleaning function.

.. code-block:: python

    def noop(x):
        return x
    data = DataLoader(['nflx'], '8-K', parser=noop)

The default cleaning function is as follows:

.. code-block:: python

    from edgar import html

    def clean(text):
        # Remove html <> tags
        text = html.remove_tags(text)
        # Remove most malformed characters
        text = html.remove_htmlbytes(text)
        # Remove newlines / tabs
        text = re.sub('[\n\t]', ' ', text)
        # Replace multiple spaces in a row with one
        text = html.compress_spaces(text)

        return text

For custom purposes, a modified cleaning function can be passed
to the dataloader.

For example, we may want to remove numerical tables from 10-Q forms.

.. code-block:: python

    from edgar import html

    def clean_tables(text):
        # Remove numerical tables
        text = html.remove_tables(text)
        # Remove html <> tags
        text = html.remove_tags(text)
        # Remove most malformed characters
        text = html.remove_htmlbytes(text)
        # Remove newlines / tabs
        text = re.sub('[\n\t]', ' ', text)
        # Replace multiple spaces in a row with one
        text = html.compress_spaces(text)

        return text
