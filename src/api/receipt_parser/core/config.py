import yaml
import logging
from .objectview import ObjectView
import json
import coloredlogs

LOGGER = logging.getLogger("parser_core.config")
coloredlogs.install(level='DEBUG', logger=LOGGER)


CONFIG_FILE = "config.yml"


def read_config(config=CONFIG_FILE):
    """
    Reads and parses a YAML configuration file.
    :param config: str
        The name of the configuration file.
    :return: ObjectView
        The parsed configuration data.
    """
    try:
        with open(config, 'rb') as stream:
            docs = yaml.safe_load(stream)
            return ObjectView(docs)
    except yaml.YAMLError as e:
        LOGGER.error(e)
