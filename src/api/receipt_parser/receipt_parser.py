from core import enhancer
from core import parse as parser
import logging

LOGGER = logging.getLogger("receipt_parser.driver")


def run(request_id="TEST"):
    LOGGER.info("Start enhance images...")
    enhancer.run()
    # read OCR text
    LOGGER.info("Start parsing OCR data...")
    receipts = parser.run()
    LOGGER.info("Parsing DONE.")

    # upload result to MongoDB

    return request_id


if __name__ == "__main__":
    run()
