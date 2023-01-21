import yaml
import logging
from .objectview import ObjectView
import json
import coloredlogs

LOGGER = logging.getLogger("parser_core.config")
coloredlogs.install(level='DEBUG', logger=LOGGER)


CONFIG_FILE = "config.yml"
HASHS_FILE = ".hashs.json"


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


def read_image_hashs(config=HASHS_FILE):
    """
    Reads image hashes from a JSON file.
    :param config: str
        The name of the JSON file.
    :return: dict
        The parsed image hashes data.
    """
    try:
        with open(config, 'r') as stream:
            return json.loads(stream.read())
    except Exception as e:
        LOGGER.error(e)


def write_image_hashs(file_name, hash_string, img_hashs, config=HASHS_FILE):
    """
    Writes image hashes to a JSON file.
    :param file_name: str
        The name of the image file.
    :param hash_string: str
        The hash of the image file.
    :param img_hashs: dict
        The current image hashes data.
    :param config: str
        The name of the JSON file.
    """
    img_hashs["records"].append({"name": file_name, "hash": hash_string})
    json_obj = json.dumps(img_hashs, indent=4)
    try:
        with open(config, 'w') as stream:
            stream.write(json_obj)
    except Exception as e:
        LOGGER.error(e)
