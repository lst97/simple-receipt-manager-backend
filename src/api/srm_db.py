import pymongo
from bson import json_util, ObjectId
from dotenv import load_dotenv
import os
from os.path import join, dirname
import coloredlogs
import logging

LOGGER = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')
coloredlogs.install(level='DEBUG', logging=LOGGER)

DB_NAME = "simple-receipt-manager"

load_dotenv(dotenv_path=join(dirname(__file__), 'config/.env'))

client = ""


def establish_connection():
    """
    Establish a connection to the MongoDB server and return a client for a specific database.
    """

    LOGGER.info("Establishing database connection.")
    # Retrieve the MongoDB connection string, admin name and password from environment variables
    connection_string = os.getenv('DB_CONNECTION_STRING')
    admin_name = os.getenv('ADMIN_NAME')
    admin_password = os.getenv('ADMIN_PASSWORD')

    # Connect to the MongoDB server
    global client
    client = pymongo.MongoClient(
        f"mongodb+srv://{admin_name}:{admin_password}@{connection_string}/test")
    LOGGER.info("Connection established.")

    return client[DB_NAME]


def close_connection():
    client.close()
    LOGGER.info("Connection closed.")


def insert_parse_queue(request_id, group_id, files):
    LOGGER.info("Insert parse queue.")
    db = establish_connection()
    parse_queue = db["parse_queue"]
    data = {
        "request_id": request_id,
        "group_id": group_id,
        "files":  files,
        "success": False
    }
    parse_queue.insert_one(data)
    close_connection()

    LOGGER.info("Insertion complete.")


def delete_parse_queue(request_id):
    LOGGER.info("Delete parse queue complete.")
    db = establish_connection()
    parse_queue_collection = db["parse_queue"]
    result = parse_queue_collection.find_one({"request_id": request_id})
    parse_queue_collection.delete_one(result)
    close_connection()
    LOGGER.info("Insert complete.")


def insert_image_hash(hashs):
    LOGGER.info("Insert image hash.")
    db = establish_connection()
    parsed_images = db["parsed_images"]
    parsed_images_id = parsed_images.find_one({}, {"_id": 1})
    result = parsed_images.update_many(
        parsed_images_id, {"$push": {"hashs": {"$each": hashs}}})

    # Check the result of the update
    if result.modified_count <= 0:
        LOGGER.error("Faile to add image hash into Database.")
        close_connection()
        LOGGER.info("Insertion fail.")
        return False

    close_connection()
    LOGGER.info("Deletetion compelete.")
    return True


def find_image_hash(hash_str):
    LOGGER.info("Find image hash.")
    db = establish_connection()
    parsed_images = db["parsed_images"]
    cursor = parsed_images.find_one({"hashs": hash_str})
    close_connection()
    LOGGER.info("Find complete.")
    return cursor if cursor is None else json_util.dumps(cursor)


def insert_record_by_group_id(receipt, group_id, request_id, file_name, image_base64, image_hash):
    LOGGER.info(f"Insert receipt record with group id {group_id}")
    db = establish_connection()
    groups = db["groups"]
    record = {}
    record["receipts"] = [receipt]
    record["request_id"] = request_id
    record["file_name"] = file_name
    record["payer"] = ''
    record["share_with"] = ''
    record["base64"] = image_base64
    record["hash"] = image_hash

    result = groups.update_one(
        {"_id": ObjectId(group_id)}, {"$push": {"records": record}})

    # Check the result of the update
    if result.modified_count <= 0:
        LOGGER.error("Faile to add record into Database.")
        close_connection()
        LOGGER.info("Insertion fail.")
        return False

    close_connection()
    LOGGER.info("Insertion complete.")
    return True


def get_groups():
    LOGGER.info("Get groups")
    db = establish_connection()
    groups_collection = db.groups
    cursor = groups_collection.find()

    LOGGER.info("Get complete.")
    return json_util.dumps(cursor)


def get_group_records(group_id, includ_image=False):
    LOGGER.info("Get group records")
    db = establish_connection()
    groups_collection = db.groups

    projection = {"records": 1}
    if not includ_image:
        del projection["records"]
        projection["records.base64"] = 0
        projection["records.hash"] = 0
        projection["records.raw"] = 0

    result = groups_collection.find_one(
        {"_id": ObjectId(group_id)}, projection)

    LOGGER.info("Get complete")
    return result


def get_groups_info():
    LOGGER.info("Get groups info")
    db = establish_connection()
    groups_collection = db.groups

    # Retrieve the name of all groups, sorted by group_number
    cursor = groups_collection.find({}, {"name": 1}).sort(
        [('group_number', pymongo.ASCENDING)])

    LOGGER.info("Get complete")
    return json_util.dumps(cursor)


def delete_parse_queue(request_id):
    LOGGER.info("Delete parse queue status")
    db = establish_connection()
    parse_queue_collection = db.parse_queue

    parse_queue_collection.delete_one({"request_id": request_id})

    LOGGER.info("Delete complete")
    return True
