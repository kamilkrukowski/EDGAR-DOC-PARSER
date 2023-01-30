"""
    Master file for training new models to predict labels
"""
import os
import sys ; sys.path.append('..')
import math


from tqdm.auto import tqdm
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, random_split
import pytorch_lightning as pl
from sklearn.metrics import roc_auc_score


import EDGAR

class BaselineNN(pl.LightningModule):

    def __init__(self, vocab_size: int, max_sentence_len: int, output_size: int, label_map: dict[int:str] = None):
        super().__init__();

        self.vocab_size = vocab_size;
        self.output_size = output_size;
        self.label_map = label_map;

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
        x, y, mask = train_batch;
        y_hat = self.forward(x)
        loss = self.loss_fn(y_hat, y)
        loss = (loss * mask).sum()
        return loss;
    
    def validation_step(self, val_batch, batch_idx):
        x, y, mask = val_batch;
        y_hat = self.forward(x)
        loss = self.loss_fn(y_hat, y)

        loss = (loss * mask).sum()
        self.log("va_loss", loss, prog_bar=True, on_epoch=True)
        self.get_metrics(y, y_hat, prefix='va_', prog_bar=True)
        return loss

    def get_metrics(self, y, y_hat, prefix=None, prog_bar=False):
        aucs = []
        for i in range(self.output_size):
            if (torch.sum(y[:,i]) == 0):
                continue;
            auc = roc_auc_score(y[:,i], y_hat[:,i])
            self.log(f"{prefix}_auc_{i}_{self.label_map[i]}", auc, on_epoch=True)
            aucs.append(auc)
        self.log(f"{prefix}max_auroc", np.max(aucs), prog_bar=prog_bar, on_epoch=True)
        #self.log(f"{prefix}mean_auroc", np.max(aucs), prog_bar=prog_bar, on_epoch=True)

        return;

# PARAMETERS

BATCH_SIZE = 512
NUM_WORKERS = 2

# EDGAR opts

data_dir = 'data'
metadata = EDGAR.metadata(data_dir=data_dir)

# List of companies to process
tikrs = open(os.path.join(metadata.path, 'tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]
tikrs = ['nflx']

dataset = EDGAR.dataloader(tikrs=tikrs, debug=True, max_sentence_len=100, sparse_weight=0.1)
label_map = dataset.label_map;

d_len = len(dataset)
tr_len = math.floor(0.8*d_len)
va_len = math.floor(0.1*d_len)
te_len = d_len - tr_len - va_len

train, val, test = random_split(dataset, [tr_len, va_len, te_len])

train_loader = DataLoader(train, batch_size=BATCH_SIZE, num_workers=NUM_WORKERS)
val_loader = DataLoader(val, batch_size=BATCH_SIZE, num_workers=NUM_WORKERS)
test_loader = DataLoader(test, batch_size=BATCH_SIZE, num_workers=NUM_WORKERS)

model = BaselineNN(vocab_size = len(dataset.vocab)+5, max_sentence_len = dataset.max_sentence_len, 
                    output_size = len(dataset.label_map)+1, label_map = {label_map[key]:key for key in label_map})

model_summary = pl.callbacks.ModelSummary(max_depth=-1)
tensorboard_logger = pl.loggers.tensorboard.TensorBoardLogger(os.path.join("..","."))
callbacks = [model_summary]

trainer = pl.Trainer(callbacks=callbacks, logger=tensorboard_logger)

trainer.fit(model, train_loader, val_loader);
