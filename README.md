# EDGAR-DOC-PARSER

## Documentation

For more information read our documentation hosted [here.](https://kamilkrukowski.github.io/EDGAR-DOC-PARSER)

## Installation Guide

We are available through [pip.](https://pypi.org/project/edgar-doc-parser/)
```
pip install edgar-doc-parser
```

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
