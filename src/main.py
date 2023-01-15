from api import srm_api
from receipt_parser import receipt_parser
import threading
import logging
import os
import signal


def exit_main():
    logging.error("Main Process Exit.")
    os.kill(os.getppid(), signal.SIGTERM)


def api_thread():
    logging.info("Simple Receipt Manager Thread - RUNNING...")
    srm_api.run()
    # if either one thread exit, the main will be exit
    logging.error("api exit unexpectedly.")
    logging.info("main process exit.")
    exit_main()


def receipt_parser_thread():
    logging.info("Receipt Parser Thread - RUNNING...")
    receipt_parser.run()
    # if either one thread exit, the main will be exit
    logging.error("receipt parser_thread exit unexpectedly.")
    logging.info("main process exit.")
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
    run()
