from core import enhancer
from core import parse as parser
import logging
from dotenv import load_dotenv
from os.path import join, dirname
import sys
import coloredlogs
import json

load_dotenv(dotenv_path=join(dirname(dirname(__file__)), 'config/.env'))

LOGGER = logging.getLogger("receipt_parser.driver")


def run(files_name):
    LOGGER.info("Start enhance images...")
    enhancer.run(files_name)
    LOGGER.info("Start parsing OCR data...")
    receipts = parser.run(files_name)
    for idx, receipt in enumerate(receipts):
        receipt["file_name"] = files_name[idx]
        receipt["receipt_no"] = ''

    sys.stdout.write(json.dumps(receipts).replace("\n", ""))

    LOGGER.info("Parsing DONE.")


if __name__ == "__main__":
    coloredlogs.install(level='DEBUG')
    coloredlogs.install(level='DEBUG', logger=LOGGER)
    number_of_files = sys.argv[1]
    files_name = []
    for i in range(int(number_of_files)):
        files_name.append(sys.argv[2 + i])

    run(files_name)
