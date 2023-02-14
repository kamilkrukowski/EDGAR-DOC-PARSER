import os
import math


import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, random_split
from sklearn.metrics import roc_auc_score
import numpy as np
from transformers import BertTokenizerFast, Trainer
from tqdm.auto import tqdm

class NLPTrainer(Trainer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    self.loss_fn = 
    def compute_loss(self, model, inputs):
        mask = inputs.get('loss_mask');
        x = inputs.get('input_ids');
        y = inputs.get('y');
        y_hat = self.model(x);
        custom_loss = self.loss_fn(y, y_hat)
        return custom_loss

class EDGARDataset(Dataset):
    def __init__(self, setting_dir_name, metadata, parser, **kwargs):
        super(Dataset).__init__()

        data_dir

        self.x = []
        self.y = []
        self.masks = []

        if type(tikrs) is str:
            tikrs = [tikrs];
        
        prep_dir = os.path.join(data_dir, "dataloader_cache", setting_dir_name)
        label_fpath = os.path.join(prep_dir, 'labels.txt')
        label_list = np.loadtxt(label_fpath)
        
        self.label_map = {y:i+1 for i,y in enumerate(label_list)}

        self.tokenizer = BertTokenizerFast.from_pretrained(prep_dir)

        sparse_weight = kwargs.get('sparse_weight', 0.5)
        non_sparse_weight = 1.0-sparse_weight
        
    def __len__(self):
        return self._len

    def __getitem__(self, idx):
        x = self.x[idx]
        y = self.y[idx]
        mask = self.masks[idx]
        return (x, y, mask)

    def tokenize(self, sentence):
        punctuation = '.!,;:\'\"()@#$%&/+=-'
        for ch in punctuation:
            sentence.replace(ch, f" {ch} ")
        for alph in '0123456789':
            sentence.replace(alph, f" <alphanumeric> ")

        return sentence.split(' ')


    def embed(self, sentence: str):
            first_token = 5;

            pad_token = 0
            unk_token = 1
            start_token = 2
            end_token = 3
            tokens = self.tokenize(sentence);

            out = torch.zeros(self.max_sentence_len).long();

            out[0] = start_token; idx = 1
            for token in tokens:
                if (token == ''): 
                    continue;
                if (idx == self.max_sentence_len-2):
                    break;
                token_id = self.vocab.get(token, unk_token)
                out[idx] = token_id
                idx += 1;
            out[idx] = end_token
            return out

# HYPER PARAMETERS
BATCH_SIZE = 512
NUM_WORKERS = 2

# EDGAR opts

data_dir = 'data'
metadata = EDGAR.metadata(data_dir=data_dir)

# List of companies to process
tikrs = open(os.path.join(metadata.path, 'tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]
tikrs = ['nflx']

dataset = EDGARDataset(tikrs=tikrs, debug=True, max_sentence_len=100, sparse_weight=0.1)
label_map = dataset.label_map;

d_len = len(dataset)
tr_len = math.floor(0.8*d_len)
va_len = math.floor(0.1*d_len)
te_len = d_len - tr_len - va_len

train, val, test = random_split(dataset, [tr_len, va_len, te_len])

train_loader = DataLoader(train, batch_size=BATCH_SIZE, num_workers=NUM_WORKERS)
val_loader = DataLoader(val, batch_size=BATCH_SIZE, num_workers=NUM_WORKERS)
test_loader = DataLoader(test, batch_size=BATCH_SIZE, num_workers=NUM_WORKERS)