from api import srm_api
import threading
import logging
import coloredlogs
import util
import time

LOGGER = logging.getLogger(__name__)


class Thread(threading.Thread):
    def run(self):
        try:
            threading.Thread.run(self)
        except Exception as err:
            self.err = err
        else:
            self.err = None


def exit_parent_process():
    LOGGER.error("Main Process Exit.")
    util.kill_parent()


def api_thread():
    LOGGER.info("Simple Receipt Manager Thread - RUNNING...")
    try:
        srm_api.run()
    except Exception as err:
        raise err


def run():
    threads = []

    while True:
        api = Thread(target=api_thread)
        api.start()
        threads.append(api)
        threads[0].join()  # only one thread at the moment

        if threads[0].err is not None:
            LOGGER.error(threads[0].err)
            threads.pop()
            LOGGER.error("api exit unexpectedly - RESTARTING...")

            # Try to restart API
            time.sleep(3)

        else:
            LOGGER.INFO("api exit - SUCCESS")
            break


if __name__ == '__main__':
    coloredlogs.install(level='DEBUG')
    coloredlogs.install(level='DEBUG', logger=LOGGER)

    run()
