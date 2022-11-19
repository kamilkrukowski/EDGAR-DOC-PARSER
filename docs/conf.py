import os; import sys;
sys.path.append(os.path.abspath('..'))

import mock
MOCK_MODULES = ['numpy', 'scipy', 'matplotlib', 'matplotlib.pyplot', 'scipy', 'torch', 
                'yaml', 'secedgar', 'selenium', 'selenium.webdriver.common.by', 'selenium.common.exceptions', 'selenium.webdriver.remote.webelement'
                'pyyaml', 'torch.utils.data', 'bs4']
for mod_name in MOCK_MODULES:
        sys.modules[mod_name] = mock.Mock()

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pyEDGAR'
copyright = '2022, Kamil Krukowski'
author = 'Kamil Krukowski'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
        'sphinx.ext.githubpages',
        'sphinx.ext.napoleon',
        'sphinx.ext.autodoc',
        'sphinx_rtd_theme'
        ]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
