import logging
import os
import random
from argparse import ArgumentParser
from pathlib import Path
from random import sample
from typing import Dict, Set, List, Tuple

from data.irt.split.split_dir import SplitDir
from data.irt.text.text_dir import TextDir
from data.power.samples.samples_dir import SamplesDir


def main():
    logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level=logging.INFO)

    args = parse_args()

    if args.random_seed:
        random.seed(args.random_seed)

    create_texter_dataset(args)

    logging.info('Finished successfully')


def parse_args():
    parser = ArgumentParser()

    parser.add_argument('split_dir', metavar='split-dir',
                        help='Path to (input) IRT Split Directory')

    parser.add_argument('text_dir', metavar='text-dir',
                        help='Path to (input) IRT Text Directory')

    parser.add_argument('samples_dir', metavar='samples-dir',
                        help='Path to (output) POWER Samples Directory')

    default_class_count = 100
    parser.add_argument('--class-count', dest='class_count', type=int, metavar='INT', default=default_class_count,
                        help='Number of classes (default: {})'.format(default_class_count))

    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help='Overwrite output files if they already exist')

    parser.add_argument('--random-seed', dest='random_seed', metavar='STR',
                        help='Use together with PYTHONHASHSEED for reproducibility')

    default_sent_count = 5
    parser.add_argument('--sent-count', dest='sent_count', type=int, metavar='INT', default=default_sent_count,
                        help='Number of sentences per entity. Entities for which not enough sentences'
                             ' are availabe are dropped. (default: {})'.format(default_sent_count))

    args = parser.parse_args()

    # Log applied config

    logging.info('Applied config:')
    logging.info('    {:24} {}'.format('split-dir', args.split_dir))
    logging.info('    {:24} {}'.format('text-dir', args.text_dir))
    logging.info('    {:24} {}'.format('samples-dir', args.samples_dir))
    logging.info('    {:24} {}'.format('--class-count', args.class_count))
    logging.info('    {:24} {}'.format('--overwrite', args.overwrite))
    logging.info('    {:24} {}'.format('--random-seed', args.random_seed))
    logging.info('    {:24} {}'.format('--sent-count', args.sent_count))

    logging.info('Environment variables:')
    logging.info('    {:24} {}'.format('PYTHONHASHSEED', os.getenv('PYTHONHASHSEED')))

    return args


def create_texter_dataset(args):
    split_dir_path = args.split_dir
    text_dir_path = args.text_dir
    samples_dir_path = args.samples_dir

    class_count = args.class_count
    overwrite = args.overwrite
    sent_count = args.sent_count

    #
    # Check that (input) IRT Split Directory exists
    #

    logging.info('Check that (input) IRT Split Directory exists ...')

    split_dir = SplitDir(Path(split_dir_path))
    split_dir.check()

    #
    # Check that (input) IRT Split Directory exists
    #

    logging.info('Check that (input) IRT Split Directory exists ...')

    text_dir = TextDir(Path(text_dir_path))
    text_dir.check()

    #
    # Check that (output) POWER Samples Directory does not exist
    #

    logging.info('Check that (output) POWER Samples Directory does not exist ...')

    samples_dir = SamplesDir(Path(samples_dir_path))
    samples_dir.create(overwrite=overwrite)

    #
    # Load IRT Triples TXTs
    #

    logging.info('Load IRT Triples TXTs ...')

    cw_train_triples: List[Tuple[int, int, int]] = split_dir.cw_train_triples_txt.load()
    cw_valid_triples: List[Tuple[int, int, int]] = split_dir.cw_valid_triples_txt.load()
    ow_valid_triples: List[Tuple[int, int, int]] = split_dir.ow_valid_triples_txt.load()
    ow_test_triples: List[Tuple[int, int, int]] = split_dir.ow_test_triples_txt.load()

    train_triples = cw_train_triples + cw_valid_triples
    valid_triples = ow_valid_triples
    test_triples = ow_test_triples

    #
    # Save triples to POWER Triples DBs
    #

    logging.info('Save triples to POWER Triples DBs ...')

    train_triples_db = samples_dir.tmp_dir.train_triples_db
    train_triples_db.create_triples_table()
    train_triples_db.insert_triples(train_triples)

    valid_triples_db = samples_dir.tmp_dir.valid_triples_db
    valid_triples_db.create_triples_table()
    valid_triples_db.insert_triples(valid_triples)

    test_triples_db = samples_dir.tmp_dir.test_triples_db
    test_triples_db.create_triples_table()
    test_triples_db.insert_triples(test_triples)

    #
    # Create Classes TSV
    #

    logging.info('Create Classes TSV ...')

    rel_tail_supps = samples_dir.tmp_dir.train_triples_db.select_top_rel_tails(class_count)

    ent_to_label = split_dir.ent_labels_txt.load()
    rel_to_label = split_dir.rel_labels_txt.load()

    ent_count = len(ent_to_label)
    rel_tail_freq_labels = [(rel, tail, supp / ent_count, f'{rel_to_label[rel]} {ent_to_label[tail]}')
                            for rel, tail, supp in rel_tail_supps]

    samples_dir.classes_tsv.save(rel_tail_freq_labels)

    #
    # Query classes' entities
    #

    logging.info("Query classes' entities ...")

    train_class_ents = []
    valid_class_ents = []
    test_class_ents = []

    for rel, tail, _ in rel_tail_supps:
        class_ents = samples_dir.tmp_dir.train_triples_db.select_heads_with_rel_tail(rel, tail)
        train_class_ents.append(class_ents)

    for rel, tail, _ in rel_tail_supps:
        class_ents = samples_dir.tmp_dir.valid_triples_db.select_heads_with_rel_tail(rel, tail)
        valid_class_ents.append(class_ents)

    for rel, tail, _ in rel_tail_supps:
        class_ents = samples_dir.tmp_dir.test_triples_db.select_heads_with_rel_tail(rel, tail)
        test_class_ents.append(class_ents)

    #
    # Create POWER Sample TSVs
    #

    logging.info('Create POWER Sample TSVs ...')

    train_ent_to_sents: Dict[int, Set[str]] = text_dir.cw_train_sents_txt.load()
    valid_ent_to_sents: Dict[int, Set[str]] = text_dir.ow_valid_sents_txt.load()
    test_ent_to_sents: Dict[int, Set[str]] = text_dir.ow_test_sents_txt.load()

    def get_samples(ent_to_sents, class_ents):
        """
        :param ent_to_sents: {ent: {sent}}
        :param class_ents: [[ent]]
        :return: [(ent, label, [has class], [sent])
        """

        ent_lbl_classes_sents_list = []

        for ent, sents in ent_to_sents.items():

            ent_classes = []
            for class_ in range(len(class_ents)):
                ent_classes.append(int(ent in class_ents[class_]))

            if len(sents) < sent_count:
                logging.warning(f"Entity '{ent_to_label[ent]}' ({ent}) has less than {sent_count} sentences. Skipping")
                continue

            some_sents = sample(sents, sent_count)

            ent_lbl_classes_sents_list.append((ent, ent_to_label[ent], ent_classes, some_sents))

        return ent_lbl_classes_sents_list

    train_samples = get_samples(train_ent_to_sents, train_class_ents)
    valid_samples = get_samples(valid_ent_to_sents, valid_class_ents)
    test_samples = get_samples(test_ent_to_sents, test_class_ents)

    samples_dir.train_samples_tsv.save(train_samples)
    samples_dir.valid_samples_tsv.save(valid_samples)
    samples_dir.test_samples_tsv.save(test_samples)


if __name__ == '__main__':
    main()
