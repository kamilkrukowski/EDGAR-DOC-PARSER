.. _setup:

Setup
============

We recommend Conda for package management.

.. code-block:: bash

    $ conda create -n edgar -c conda-forge scipy numpy selenium=4.5.0 pyyaml chardet requests lxml pandas
    $ conda activate edgar
    $ pip install secedgar==0.4.0 beautifulsoup4 attrs typing-extensions