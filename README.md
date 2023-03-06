# EDGAR-DOC-PARSER

## Installation Guide

We are available through [pip.](https://pypi.org/project/edgar-doc-parser/)
```
pip install edgar-doc-parser
```

## About

A package for downloading, extracting, parsing, and processing data from SEC-EDGAR, a public online database of all documents filed with the USA's Securities and Exchange Commission.

## Documentation

For more information read our documentation hosted [here.](https://kamilkrukowski.github.io/EDGAR-DOC-PARSER)

## Quick Start Guide

```
import edgar

dataloader = edgar.Dataloader(tikrs=['nflx'], document_type='8-K', data_dir='data')

for text_8k in dataloader:
  #dostuff
  print(text_8k)
  break
```

## Currently Support Filing Types

* 10-Q
* 8-K

We plan on expanding the list in future releases

## Dependencies
### Local - Conda

To create conda environment for local
```
conda create -n edgar -c conda-forge -c anaconda python=3.10 scipy numpy pyyaml pandas
conda activate edgar
pip install secedgar==0.4.0
```
