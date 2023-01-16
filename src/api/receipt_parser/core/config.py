import yaml
import logging
from .objectview import ObjectView

LOGGER = logging.getLogger("parser_core.config")


def read_config(config="config.yml"):
    """
    :param file: str
        Name of file to read
    :return: ObjectView
        Parsed config file
    """
    with open(config, 'rb') as stream:
        try:
            docs = yaml.safe_load(stream)
            return ObjectView(docs)
        except yaml.YAMLError as e:
            logging.error(e)
