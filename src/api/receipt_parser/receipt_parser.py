from core import enhancer
from core import parse as parser
import logging
import requests
from dotenv import load_dotenv
from os.path import join, dirname
import os
import sys
import coloredlogs

load_dotenv(dotenv_path=join(dirname(dirname(__file__)), 'config/.env'))

LOGGER = logging.getLogger("receipt_parser.driver")


def get_files_from_api(request_id):
    response = requests.get(
        '{0}/internal/parse/{1}'.format(os.getenv("SRM_API_URL"), request_id))

    files = []
    if response.status_code == 200:
        json_data = response.json()
        for files_obj in json_data["files"]:
            files.append(files_obj["file_name"])

    return files


def run(request_id):
    LOGGER.info("Get files info from API")
    files_name = get_files_from_api(request_id)
    LOGGER.info("Start enhance images...")
    # TODO: handle list of files_name input and enhance it according to the list
    enhancer.run(files_name)
    # read OCR text
    LOGGER.info("Start parsing OCR data...")
    receipts = parser.run()
    LOGGER.info("Parsing DONE.")

    # upload result to MongoDB

    return request_id


if __name__ == "__main__":
    coloredlogs.install(level='DEBUG')
    coloredlogs.install(level='DEBUG', logger=LOGGER)
    request_id = sys.argv[1]
    run(request_id)
