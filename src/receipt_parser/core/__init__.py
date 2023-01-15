from .config import read_config
from .parse import *
from os.path import join, dirname


def main():
    config = read_config(join(
        dirname(__file__), '../config/config.yml'))

    receipt_files = get_files_in_folder(config.receipts_path)
    stats = ocr_receipts(config, receipt_files)
    # output_statistics(stats)
