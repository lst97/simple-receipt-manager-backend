import os
import signal


def kill_parent():
    os.kill(os.getppid(), signal.SIGTERM)
