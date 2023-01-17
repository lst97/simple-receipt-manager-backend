from core import enhancer
from core import parse as parser
import logging

LOGGER = logging.getLogger("receipt_parser.driver")


def run():
    LOGGER.info("Start enhance images...")
    enhancer.run()
    # read OCR text
    LOGGER.info("Start parsing OCR data...")
    parsed_result = parser.run()
    LOGGER.info("Parsing DONE.")

    pass
    # upload result to MongoDB


if __name__ == "__main__":
    run()
