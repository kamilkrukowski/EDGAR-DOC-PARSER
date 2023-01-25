import os
import sys ; sys.path.append('..')
import argparse
import warnings
import math


from tqdm.auto import tqdm
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, random_split
import pytorch_lightning as pl


import EDGAR

class BaselineNN(pl.LightningModule):

    def __init__(self, vocab_size: int, max_sentence_len: int, output_size: int):
        super().__init__();

        self.vocab_size = vocab_size;
        self.output_size = output_size;

        self.EMBED_DIM = 32

        self.nn = nn.Sequential(
            nn.Embedding(vocab_size, self.EMBED_DIM),
            nn.Flatten(),
            nn.Linear(self.EMBED_DIM*max_sentence_len, 64*max_sentence_len),
            nn.Linear(64*max_sentence_len, 1024),
            nn.Linear(1024, output_size*2)
        )

        self.loss_fn = nn.BCELoss(reduction='none');

    def forward(self, x):
        logits = self.nn(x).reshape((-1, self.output_size, 2))
        return F.softmax(logits, dim=2)[:,:,0]

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        return optimizer

    def training_step(self, train_batch, batch_idx):
        x, y, *mask = train_batch;
        z = self.forward(x)
        loss = self.loss_fn(self.forward(x), y)
        loss = loss.sum()
        return loss;
    
    def validation_step(self, val_batch, batch_idx):
        x, y, *mask = val_batch;
        z = self.forward(x)
        loss = self.loss_fn(self.forward(x), y)

        loss=  loss.sum()
        self.log("va_loss", loss, prog_bar=True)
        return loss

    def get_metrics(self, batch, idx, prefix=None):
        return;

# PARAMETERS

BATCH_SIZE = 512
NUM_WORKERS = 16

# EDGAR opts

data_dir = 'data'
metadata = EDGAR.metadata(data_dir=data_dir)

# List of companies to process
tikrs = open(os.path.join(metadata.path, 'tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]

dataset = EDGAR.dataloader(tikrs=tikrs, debug=True, max_sentence_len=100)

d_len = len(dataset)
tr_len = math.floor(0.8*d_len)
va_len = math.floor(0.1*d_len)
te_len = d_len - tr_len - va_len

train, val, test = random_split(dataset, [tr_len, va_len, te_len])

train_loader = DataLoader(train, batch_size=BATCH_SIZE, num_workers=NUM_WORKERS)
val_loader = DataLoader(val, batch_size=BATCH_SIZE, num_workers=NUM_WORKERS)
test_loader = DataLoader(test, batch_size=BATCH_SIZE, num_workers=NUM_WORKERS)

model = BaselineNN(vocab_size = len(dataset.vocab)+5, max_sentence_len = dataset.max_sentence_len, output_size = len(dataset.labels)+1)

trainer = pl.Trainer()

trainer.fit(model, train_loader, val_loader);
