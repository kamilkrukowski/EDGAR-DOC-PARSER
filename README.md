# FinDocNLP

## Documentation

For more information read our documentation hosted [here.](https://kamilkrukowski.github.io/FinDocNLP)

## Useful information

First set of tickers to investigate in `tickers.txt`

Bulk SEC EDGAR (CIKs)
```https://www.sec.gov/Archives/edgar/cik-lookup-data.txt```

## Dependencies
### Conda

To create conda environment:
```
conda create -n edgar -c conda-forge -c anaconda python=3.10 pytorch scipy numpy selenium=4.5.0 pyyaml chardet requests lxml pandas
conda activate edgar
pip install secedgar==0.4.0 beautifulsoup4 attrs typing-extensions
pip install transformers
```

### Firefox's Geckodriver
The Data Pipeline requires a Firefox WebDriver for Selenium

Linux Guide:
```
wget https://github.com/mozilla/geckodriver/releases/download/v0.31.0/geckodriver-v0.31.0-linux32.tar.gz 
tar -xvf geckodriver-v0.26.0-linux64.tar.gz 
mv geckodriver /usr/local/bin/
cd /usr/local/bin/
chmod +x geckodriver 
```

MacOS Guide:
With MacOS, Homebrew is the quickest way to install the Firefox Webdriver.
```
brew install geckodriver
brew install firefox
```
