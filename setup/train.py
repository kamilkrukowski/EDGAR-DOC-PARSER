import os
import sys ; sys.path.append('..')
import argparse
import warnings


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

        self.nn = nn.Sequential(
            nn.Embedding(vocab_size, 256),
            nn.Flatten(),
            nn.Linear(256*max_sentence_len, 64*max_sentence_len),
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
        print(z.sum())
        loss = self.loss_fn(y, self.forward(x))
        return loss.sum();


data_dir = 'data'
metadata = EDGAR.metadata(data_dir=data_dir)

# List of companies to process
tikrs = open(os.path.join(metadata.path, 'tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]

dataset = EDGAR.dataloader(tikrs=tikrs, debug=True, max_sentence_len=1342)

train, val, test = random_split(dataset, [0.8,0.1,0.1])

train_loader = DataLoader(train, batch_size=64)
val_loader = DataLoader(val, batch_size=64)
test_loader = DataLoader(test, batch_size=64)

model = BaselineNN(vocab_size = len(dataset.vocab), max_sentence_len = dataset.max_sentence_len, output_size = len(dataset.labels))

trainer = pl.Trainer()

trainer.fit(model, train_loader, val_loader);