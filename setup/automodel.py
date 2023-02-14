import os
import math
import sys
sys.path.append('../src')


import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, random_split
import datasets
import evaluate
from sklearn.metrics import roc_auc_score
import numpy as np
from transformers import BertTokenizerFast, Trainer, AutoModelForSequenceClassification, AutoConfig
import transformers
from tqdm.auto import tqdm


import EDGAR


class NLPTrainer(Trainer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compute_loss(self, model, inputs):
        mask = inputs.get('loss_mask');
        x = inputs.get('input_ids');
        y = inputs.get('y');
        y_hat = model(x);
        custom_loss = F.binary_cross_entropy(y, y_hat, reduction=None);
        custom_loss = custom_loss * mask
        custom_loss = custom_loss.sum();
        return custom_loss

# HYPER PARAMETERS
MODEL_CONFIG_NAME = 'distilbert-base-uncased'
BATCH_SIZE = 512
NUM_WORKERS = 2
PREPROCESS_PIPE_NAME = 'DEFAULT'
PROBLEM_TYPE ='single_label_classification'
#PROBLEM_TYPE="multi_label_classification"

# EDGAR opts

data_dir = os.path.join('..','data')
setting_dir_name = 'DEFAULT'
metadata = EDGAR.metadata(data_dir=data_dir)

# List of companies to process
tikrs = open(os.path.join('..', 'tickers.txt')).read().strip()
tikrs = [i.split(',')[0].lower() for i in tikrs.split('\n')]
tikrs = ['nflx']

# loading setup
vocab_dir = os.path.join(metadata.data_dir, "dataloader_cache")
out_dir = os.path.join(vocab_dir, PREPROCESS_PIPE_NAME);
        
#label mapping
label_fpath = os.path.join(out_dir, 'labels.txt')
label_list = np.loadtxt(label_fpath, dtype=str)
label_map = {y:i+1 for i,y in enumerate(label_list)}
label_map['[UNKNOWN]'] = 0

num_labels = len(open(os.path.join(out_dir, 'labels.txt')).read().strip().split('\n')) + 1
label2id = label_map;
id2label = {label2id[key]:key for key in label2id};

# Load DATASET
features = datasets.Features({"x":datasets.Value(dtype='string'), 
    "labels": datasets.ClassLabel(num_classes=len(label_map)+1, names=['UNKNOWN', *list(label_map.keys())])})

train_inputs_fpath = os.path.join(out_dir, 'train_inputs.csv')
train_dataset = datasets.load_dataset('csv', data_files=train_inputs_fpath, column_names=list(features.keys()), features=features,
        delimiter='\t', download_mode=datasets.DownloadMode.FORCE_REDOWNLOAD)

features2 = datasets.Features({"x":datasets.Value(dtype='string'), 
    "labels": datasets.ClassLabel(num_classes=len(label_map)+1, names=['UNKNOWN', *list(label_map.keys())])})

val_inputs_fpath = os.path.join(out_dir, 'val_inputs.csv')
val_dataset = datasets.load_dataset('csv', data_files=val_inputs_fpath, column_names=list(features2.keys()), features=features2,
        delimiter='\t', download_mode=datasets.DownloadMode.FORCE_REDOWNLOAD)


# CREATE tokenizer
tokenizer = transformers.BertTokenizer.from_pretrained(MODEL_CONFIG_NAME)
def tokenize(text: str, unwrap: bool = False):
    out = tokenizer.encode(text, return_tensors='pt', padding='max_length', truncation=True, max_length=400)
    if unwrap:
        return out[0];
    return out;

# CREATE MODEL
model = transformers.AutoModelForSequenceClassification.from_pretrained(
    MODEL_CONFIG_NAME, num_labels=num_labels, label2id=label2id, id2label=id2label,
    problem_type=PROBLEM_TYPE);

# SET UP TRAINING PARAMETERS
training_args = transformers.TrainingArguments(
    output_dir="test_trainer", evaluation_strategy="steps",
    eval_steps=10, save_steps=10, logging_steps=10)
accuracy = evaluate.load("accuracy")
auroc = evaluate.load("roc_auc")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return {'accuracy': accuracy.compute(predictions=predictions, references=labels),
            'roc_auc': auroc.compute(predictions=predictions, references=labels)}

train_dataset['train'] = train_dataset['train'].map(lambda batch: {"input_ids" : tokenize(batch["x"], unwrap=True)})
val_dataset['train'] =   val_dataset['train'].map(lambda batch: {"input_ids" : tokenize(batch["x"], unwrap=True)})
trainer = Trainer(model=model,
            args=training_args,
            train_dataset = train_dataset['train'].shuffle(seed=17), 
            eval_dataset = val_dataset['train'].shuffle(seed=17),
            compute_metrics = compute_metrics
        )
trainer.train()