from torch.utils.data import Dataset
import torch
import numpy as np


import pickle as pkl
import os


"""
    Constructor: (data_dir)
"""
class EDGARDataset(Dataset):
    def __init__(self, data_dir = 'data'):
        super(Dataset).__init__()
        
    def __len__(self):
        return self._len

    def __getitem__(self, idx):
        x = self.fps[idx]
        y = self.msms[idx]
        mask = self.masks[idx]
        return (x, y, mask)


if __name__ == '__main__':
    dataset = EDGARDataset();

    for x, y in dataset:
        print(f"training data shape is {x.shape}")
        print(f"Mass spec label shape is {y.shape}")
        break;
