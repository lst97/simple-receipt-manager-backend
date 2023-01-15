from api import srm_api
from receipt_parser import receipt_parser
import threading
import logging
import coloredlogs
import os
import signal

LOGGER = logging.getLogger(__name__)


def exit_main():
    LOGGER.error("Main Process Exit.")
    os.kill(os.getppid(), signal.SIGTERM)


def api_thread():
    LOGGER.info("Simple Receipt Manager Thread - RUNNING...")
    srm_api.run()
    # if either one thread exit, the main will be exit
    LOGGER.error("api exit unexpectedly.")
    exit_main()


def receipt_parser_thread():
    LOGGER.info("Receipt Parser Thread - RUNNING...")
    receipt_parser.run()
    # if either one thread exit, the main will be exit
    LOGGER.error("receipt_parser_thread exit unexpectedly.")
    exit_main()


def run():
    threads = []
    api = threading.Thread(target=api_thread)
    receipt_parser = threading.Thread(target=receipt_parser_thread)
    threads.append(api)
    threads.append(receipt_parser)

    api.start()
    receipt_parser.start()

    for thread in threads:
        thread.join()


if __name__ == '__main__':
    coloredlogs.install(level='DEBUG')
    coloredlogs.install(level='DEBUG', logger=LOGGER)

    run()
