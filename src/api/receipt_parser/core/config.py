import yaml
import logging
from .objectview import ObjectView
import json
import coloredlogs

LOGGER = logging.getLogger("parser_core.config")
coloredlogs.install(level='DEBUG', logger=LOGGER)


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
            LOGGER.error(e)


def read_image_hashs(config=".hashs.json"):
    with open(config, 'r') as stream:
        return json.loads(stream.read())


def write_image_hashs(file_name, hash_string, img_hashs, config=".hash.json"):
    img_hashs["records"].append({"name": file_name, "hash": hash_string})
    json_obj = json.dumps(img_hashs, indent=4)
    with open(config, 'w') as stream:
        stream.write(json_obj)
