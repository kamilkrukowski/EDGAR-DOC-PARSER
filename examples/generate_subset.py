import os
import sys ; sys.path.append('..')

from tqdm.auto import tqdm
import numpy as np
import argparse
import warnings


import EDGAR

def test_subset_tikrs(s):
	print("test_subset_tikrs")
	print("Test Case #1: generate subset that has the [\"nflx\",\"atvi\"] ")
	res1 = s.subset( data = None, labels = None, 
		tikrs= ["nflx","atvi"], save = False,keywords = None, fname = "subset.npy")
	check = True
	for val in res1:
		if(val[4] not in ["nflx","atvi"]):
			print("something is wrong with the test_subset_tikrs: Test Case #1")
			print("this is wrong:", val,"\n\n\n\n")
			check = False
	if check:
		print("Test Case #1 pass\n\n\n\n")

	print("Test Case #2: generate subset that has the label = ['dei:DocumentTransitionReport'] and tikrs = ['nflx', 'atvi','gs']")
	res2 = s.subset( data = None, labels = [ 'dei:DocumentTransitionReport'], tikrs= ['nflx', 'atvi','gs'], save = False,keywords = None, fname = "subset.npy")
	print(res2, "\n\n\n\n\n")

	print("Test Case #3: generate subset that has the label = ['dei:DocumentTransitionReport'] and tikrs = []")
	res3 = s.subset( data = None, labels = [ 'dei:DocumentTransitionReport'], tikrs= [], save = False,keywords = None, fname = "subset.npy")
	print(res3, "\n\n\n\n\n")

def test_subset_labels(s):
	print("test_subset_labels")
	print("Test Case #1: generate subset that has the label = 'dei:DocumentTransitionReport'")
	res1 = s.subset( data = None, labels = [ 'dei:DocumentTransitionReport'], 
		tikrs= None, save = False,keywords = None, fname = "subset.npy")
	print(res1, "\n\n\n\n\n")

	print("Test Case #2: select data where the label occurs more than a certain number of times (> 100)")
	valid_labels, label_counts = s.label_frequency(min_percent = 0.0, min_occurence = 100)
	print("valid labels:",[(label, label_counts[label])for label in valid_labels])
	res2 = s.subset( data = None, labels = valid_labels, tikrs= None, save = False,keywords = None, fname = "subset.npy")
	print(res2, "\n\n\n\n\n")


def test_keywords_keywords(s):
	print("test_subset_keywords")
	print("Test Case #1: generate subset that has the keyword '☐' ")
	res1 = s.subset( data = None, labels = None, 
		tikrs= None, save = True,keywords = ['☐'], fname = "subset.npy")
	print( res1, "\n\n\n\n\n")

	print("Test Case #2: generate subset that has the keyword 'revenue' and label = 'dei:DocumentTransitionReport'")
	res2 = s.subset( data = None, labels = ['dei:DocumentTransitionReport'], 
		tikrs= None, save = False,keywords = ['revenue'], fname = "subset.npy")
	print("expected res: [] \nactual res:", res2, "\n\n\n\n\n")

data_dir = 'data'
metadata = EDGAR.metadata(data_dir=data_dir)
loader = EDGAR.downloader(data_dir=data_dir);
parser = EDGAR.parser(data_dir=data_dir)

# List of companies to process
tikrs = open(os.path.join(metadata.path, 'tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]
#tikrs = ['nflx']

s = EDGAR.subset(tikrs=tikrs, debug=True)
#print(d.raw_data)


#minimum percentage of a certain label and a minimum occurence of the label
#valid_labels, label_counts = s.label_frequency(min_percent = 0.0, min_occurence = 20)
#valid_labels: label that reach minimum percentage of a certain label and a minimum occurence of the label
#label_counts: the occurence of all the labels

valid_words, word_counts = s.word_frequency(min_percent = 0.0, min_occurence = 2000)
print(valid_words,"\n" ,word_counts)

###TEST CASE
#test_subset_labels(s)
#test_subset_tikrs(s)
#test_keywords_keywords(s)


#### Load the saved tokenizer
tokenizer = s.build_tokenizer()

# Use the tokenizer to encode the text data
#encoded_data = [tokenizer.encode(text, add_special_tokens=True) for text in text_data]

# Show the encoded data
#print("\n",tokenizer.get_vocab())
print(type(tokenizer))


stop_words = s.load_stopword() 
print(stop_words)



