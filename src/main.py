from api import srm_api
import threading
import logging
import coloredlogs
import util
import time

"""
- LOGGER is an instance of the python logging class, it will be used to log information and error messages.
- exit_parent_process() is a function that will exit the parent process if the API thread failed to start after 3 attempts.
- api_thread() is a function that runs the API, it will be run by the thread.
- run() function is the main function that starts the API thread, it will try to run the thread 3 times before calling exit_parent_process() function if the thread still failed to run after 3 attempts.
- coloredlogs.install(level='DEBUG') and coloredlogs.install(level='DEBUG', logger=LOGGER) are used to set the log level and to show the log message with color.
- The if __name__ == '__main__': statement is used to ensure that the code is only executed if the script is run directly, not when it is imported as a module.
"""
LOGGER = logging.getLogger(__name__)

# Function to exit the parent process


def exit_parent_process():
    LOGGER.error("Main Process Exit.")
    util.kill_parent()

# Function that runs the API


def api_thread():
    LOGGER.info("Simple Receipt Manager Thread - RUNNING...")
    try:
        srm_api.run()
    except Exception as err:
        LOGGER.error(err)


def run():
    LOGGER.info("API thread start")

    # Try to run the API thread 3 times
    for i in range(3):
        api = threading.Thread(target=api_thread)
        api.start()
        # Wait for the thread to complete
        api.join()
        if not api.is_alive():
            LOGGER.info("API thread exits successfully")
            break
        else:
            LOGGER.error("API thread failed, retrying in 3 seconds")
            time.sleep(3)
    else:
        LOGGER.error("API thread failed to start after 3 attempts.")
        exit_parent_process()

    LOGGER.info("Main process exit successfully.")


if __name__ == '__main__':
    coloredlogs.install(level='DEBUG')
    coloredlogs.install(level='DEBUG', logger=LOGGER)

    run()
