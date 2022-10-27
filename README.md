# FinDocNLP

First set of tickers to investigate in `tickers.txt`

Bulk SEC EDGAR (CIKs)
```https://www.sec.gov/Archives/edgar/cik-lookup-data.txt```

## Dependencies
### Conda

To create conda environment:
```
conda create -n edgar scipy numpy selenium pyyaml chardet requests lxml pandas
conda activate edgar
pip install secedgar==0.4.0 beautifulsoup4 attrs typing-extensions
```

### Firefox's Geckodriver
The Data Pipeline requires a FireFox WebDriver for Selenium

Linux Guide:
```
wget https://github.com/mozilla/geckodriver/releases/download/v0.31.0/geckodriver-v0.31.0-linux32.tar.gz 
tar -xvf geckodriver-v0.26.0-linux64.tar.gz 
mv geckodriver /usr/local/bin/
cd /usr/local/bin/
chmod +x geckodriver 
```
### API Information
Fill out `apikeys.yaml` with relevant fields

