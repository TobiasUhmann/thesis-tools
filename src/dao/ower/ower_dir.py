"""
The `OWER Directory` contains the input files required for training the
`OWER Classifier`. The `OWER Temp Directory` keeps intermediate files
for debugging purposes.

**Structure**

::

    ower/                 # OWER Directory

        tmp/              # OWER Temp Directory

        ent_labels.txt    # OWER Entity Labels TXT
        rel_labels.txt    # OWER Relation Labels TXT

        classes.tsv       # OWER Classes TSV

        test.tsv          # OWER Test Samples TSV
        train.tsv         # OWER Train Samples TSV
        valid.tsv         # OWER Valid Samples TSV

|
"""

from pathlib import Path
from typing import List, Tuple

from torchtext.data import Field, TabularDataset
from torchtext.vocab import Vocab

from dao.base_dir import BaseDir
from dao.ower.samples_tsv import SamplesTsv


class OwerDir(BaseDir):
    tmp_dir: TmpDir

    ent_labels_txt: LabelsTxt
    rel_labels_txt: LabelsTxt

    classes_tsv: ClassesTsv

    train_samples_tsv: SamplesTsv
    valid_samples_tsv: SamplesTsv
    test_samples_tsv: SamplesTsv

    def __init__(self, name: str, path: Path):
        super().__init__(name, path)

        self.tmp_dir = TmpDir('OWER Temp Directory', path.joinpath('tmp'))

        self.ent_labels_txt = LabelsTxt('OWER Entity Labels TXT', path.joinpath('ent_labels.txt'))
        self.rel_labels_txt = LabelsTxt('OWER Relation Labels TXT', path.joinpath('rel_labels.txt'))

        self.classes_tsv = ClassesTsv('OWER Classes TSV', path.joinpath('classes.tsv'))

        self.train_samples_tsv = SamplesTsv('OWER Train Samples TSV', path.joinpath('train.tsv'))
        self.valid_samples_tsv = SamplesTsv('OWER Valid Samples TSV', path.joinpath('valid.tsv'))
        self.test_samples_tsv = SamplesTsv('OWER Test Samples TSV', path.joinpath('test.tsv'))

    def check(self) -> None:
        super().check()

        self.tmp_dir.check()

        self.ent_labels_txt.check()
        self.rel_labels_txt.check()

        self.classes_tsv.check()

        self.train_samples_tsv.check()
        self.valid_samples_tsv.check()
        self.test_samples_tsv.check()
