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
    client = pymongo.MongoClient(
        f"mongodb+srv://{admin_name}:{admin_password}@{connection_string}/test")
    LOGGER.info("Connection established.")

    return client


def insert_parse_queue(request_id, group_id, files):
    LOGGER.info("Insert parse queue.")
    client = establish_connection()
    db = client[DB_NAME]

    parse_queue = db["parse_queue"]
    data = {
        "request_id": request_id,
        "group_id": group_id,
        "files":  files,
        "success": False
    }
    parse_queue.insert_one(data)
    client.close()

    LOGGER.info("Insertion complete.")


def insert_image_hash(hashs):
    LOGGER.info("Insert image hash.")
    client = establish_connection()
    db = client[DB_NAME]
    parsed_images = db["parsed_images"]
    parsed_images_id = parsed_images.find_one({}, {"_id": 1})
    result = parsed_images.update_many(
        parsed_images_id, {"$push": {"hashs": {"$each": hashs}}})

    # Check the result of the update
    if result.modified_count <= 0:
        LOGGER.error("Faile to add image hash into Database.")
        client.close()
        LOGGER.info("Insertion fail.")
        return False

    client.close()
    LOGGER.info("Deletetion compelete.")
    return True


def find_image_hash(hash_str):
    LOGGER.info("Find image hash.")
    client = establish_connection()
    db = client[DB_NAME]
    parsed_images = db["parsed_images"]
    cursor = parsed_images.find_one({"hashs": hash_str})
    client.close()
    LOGGER.info("Find complete.")
    return cursor if cursor is None else json_util.dumps(cursor)


def insert_upload_receipts(user_request):
    LOGGER.info(
        f"Insert receipt record with group id {user_request['group_id']}")
    client = establish_connection()
    db = client[DB_NAME]
    groups = db["groups"]

    result = groups.update_one(
        {"_id": ObjectId(user_request['group_id'])}, {"$push": {"records": {"$each": user_request["files"]}}})

    # Check the result of the update
    if result.modified_count <= 0:
        LOGGER.error("Faile to add record into Database.")
        client.close()
        LOGGER.info("Insertion fail.")
        return False

    client.close()
    LOGGER.info("Insertion complete.")
    return True


def get_groups():
    LOGGER.info("Get groups")
    client = establish_connection()
    db = client[DB_NAME]
    groups_collection = db.groups
    cursor = groups_collection.find()

    cursor = json_util.dumps(cursor)
    client.close()
    LOGGER.info("Get complete.")
    return cursor


def get_group_records(group_id, includ_image=False):
    LOGGER.info("Get group records")
    client = establish_connection()
    db = client[DB_NAME]
    groups_collection = db.groups

    projection = {"records": 1}
    if not includ_image:
        del projection["records"]
        projection["records.base64"] = 0
        projection["records.hash"] = 0
        # projection["records.raw"] = 0

    result = groups_collection.find_one(
        {"_id": ObjectId(group_id)}, projection)

    client.close()
    LOGGER.info("Get complete")
    return result


def get_groups_info():
    LOGGER.info("Get groups info")
    client = establish_connection()
    db = client[DB_NAME]
    groups_collection = db.groups

    cursor = groups_collection.find({}, {"name": 1, "users": 1, "_id": 1}).sort(
        [('group_number', pymongo.ASCENDING)])

    response = json_util.dumps(cursor)
    client.close()
    LOGGER.info("Get complete")
    return response


def get_pending_queue(request_id):
    client = establish_connection()
    db = client[DB_NAME]
    parse_queue = db["pending_queue"]
    cursor = parse_queue.find_one(
        {"request_id": request_id}, {"request_id": 1, "_id": 0})

    cursor = json_util.dumps(cursor)
    client.close()
    return cursor


def insert_pending_queue(request_id):
    client = establish_connection()
    db = client[DB_NAME]
    pending_queue = db["pending_queue"]
    pending_queue_id = pending_queue.find_one(
        {}, {"request_id": 0, "_id": 1})

    result = pending_queue.update_one(
        pending_queue_id, {"$push": {"request_id": request_id}})

    # Check the result of the update
    if result.modified_count <= 0:
        LOGGER.error("Faile to add record into Database.")
        client.close()
        LOGGER.info("Insertion fail.")
        return False

    client.close()
    LOGGER.info("Insertion complete.")
    return True


def get_users_by_group_id(group_id):
    client = establish_connection()
    db = client[DB_NAME]
    groups_collection = db.groups

    result = groups_collection.find_one(
        {"_id": ObjectId(group_id)}, {"users": 1})

    response = json_util.dumps(result)
    client.close()
    return response


def get_group(group_id):
    client = establish_connection()
    db = client[DB_NAME]
    groups = db["groups"]
    cursor = groups.find_one(
        {"_id": ObjectId(group_id)}, {"_id": 1})

    cursor = json_util.dumps(cursor)
    client.close()
    return cursor


def insert_users(group_id, users: list):
    client = establish_connection()
    db = client[DB_NAME]
    groups = db["groups"]

    result = groups.update_one(
        {"_id": ObjectId(group_id)}, {"$addToSet": {"users": {"$each": users}}})

    # Check the result of the update
    if result.modified_count <= 0:
        LOGGER.error("Faile to add record into Database.")
        client.close()
        LOGGER.info("Insertion fail.")
        return False

    client.close()
    LOGGER.info("Insertion complete.")
    return True


def delete_pending_queue(request_id):
    client = establish_connection()
    db = client[DB_NAME]
    pending_queue = db["pending_queue"]
    pending_queue.update_one({"request_id": request_id}, {
        "$pull": {"request_id": request_id}})
    client.close()
