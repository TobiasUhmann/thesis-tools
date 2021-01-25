import os
from typing import Callable, List, Optional, Tuple, Any

import torch
from pytorch_lightning import LightningDataModule
from torch import Tensor, tensor
from torch.types import Device
from torch.utils.data import DataLoader, random_split
from torchtext.data import Dataset
from torchtext.datasets import text_classification

BATCH_SIZE = 16
NGRAMS = 2


class DataModule(LightningDataModule):
    train_dataset: Dataset
    valid_dataset: Dataset
    test_dataset: Dataset

    def prepare_data(self, pre_process: Callable[[str], List[int]]):
        if not os.path.isdir('data/'):
            os.mkdir('data/')

        ag_news = text_classification.DATASETS['AG_NEWS']
        train_valid_set, test_set = ag_news(root='data/', ngrams=NGRAMS, vocab=None)

        train_len = int(len(train_valid_set) * 0.7)
        valid_len = len(train_valid_set) - train_len
        train_set, valid_set = random_split(train_valid_set, [train_len, valid_len])

        self.train_dataset = train_set
        self.valid_dataset = valid_set
        self.test_dataset = test_set

    def setup(self, stage: Optional[str] = None):
        pass

    #
    # DataLoader methods
    #

    def train_dataloader(self) -> DataLoader:
        return DataLoader(self.train_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=generate_batch)

    def val_dataloader(self) -> DataLoader:
        return DataLoader(self.valid_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=generate_batch)

    def test_dataloader(self) -> DataLoader:
        return DataLoader(self.test_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=generate_batch)

    #
    # Other methods
    #

    def transfer_batch_to_device(self, batch: Any, device: Device) -> Any:
        pass


def generate_batch(label_tokens_batch: List[Tuple[int, Tensor]]) -> Tuple[Tensor, Tensor, Tensor]:
    """
    Split (label, tokens) batch and transform tokens into EmbeddingBag format.

    :return: 1. Concated tokens of all texts, Tensor[]
             2. Token offsets where texts begin, Tensor[batch_size]
             3. Labels for texts, Tensor[batch_size]
    """

    label_batch = tensor([entry[0] for entry in label_tokens_batch])
    tokens_batch = [entry[1] for entry in label_tokens_batch]

    token_count_batch = [len(tokens) for tokens in tokens_batch]

    offset_batch = tensor([0] + token_count_batch[:-1]).cumsum(dim=0)
    concated_tokens_batch = torch.cat(tokens_batch)

    return concated_tokens_batch, offset_batch, label_batch