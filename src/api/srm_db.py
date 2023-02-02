# Importing necessary libraries
from os.path import join, dirname
import os
import logging
import coloredlogs
from bson import json_util, ObjectId
import pymongo
from dotenv import load_dotenv

LOGGER = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')
coloredlogs.install(level='DEBUG', logging=LOGGER)

DB_NAME = "simple-receipts-manager"

load_dotenv(dotenv_path=join(dirname(__file__), 'config/.env'))


class MongoDB():
    def __init__(self) -> None:
        self.connection_string = os.getenv('DB_CONNECTION_STRING')
        self.admin_name = os.getenv('ADMIN_NAME')
        self.admin_password = os.getenv('ADMIN_PASSWORD')

    def _get_pending_queue_object_id(self):
        LOGGER.info("Get pending queue.")
        with self._establish_connection() as client:
            db = client[DB_NAME]
            pending_queue = db["pending_queue"]
            return pending_queue.find_one(
                {}, {"request_id": 0, "_id": 1})

    def _establish_connection(self):
        # client = pymongo.MongoClient(
        #     f"mongodb+srv://{self.admin_name}:{self.admin_password}@{self.connection_string}/test")
        client = pymongo.MongoClient('mongodb://localhost:27017')
        return client

    # IMAGE HASH RELATED
    def insert_image_hash(self, hashs):
        LOGGER.info("Insert image hash.")
        with self._establish_connection() as client:
            db = client[DB_NAME]
            parsed_images = db["parsed_images"]
            result = parsed_images.update_many(
                self.parsed_images_object_id, {"$push": {"hashs": {"$each": hashs}}})

            # Check the result of the update
            if result.modified_count <= 0:
                LOGGER.error("Faile to add image hash into Database.")
                return False

            return True

    def find_image_hash(self, hash_str):
        LOGGER.info("Find image hash.")
        with self._establish_connection() as client:
            db = client[DB_NAME]
            parsed_images = db["parsed_images"]
            result = parsed_images.find_one({"hashs": hash_str})
        LOGGER.info("Find complete.")
        return result if result is None else json_util.dumps(result)

    # GROUP RELATED
    def insert_upload_receipts(self, user_request):
        LOGGER.info(
            f"Insert receipt record with group id {user_request['group_id']}")
        with self._establish_connection() as client:
            db = client[DB_NAME]
            groups = db["groups"]

            result = groups.update_one(
                {"_id": ObjectId(user_request['group_id'])}, {
                    "$push": {"records": {"$each": user_request["files"]}}}
            )

            if result.modified_count <= 0:
                LOGGER.error("Faile to add record into Database.")
                return False

            return True

    def get_group(self, group_id):
        LOGGER.info(f"Get group {group_id}")
        with self._establish_connection() as client:
            db = client[DB_NAME]
            groups = db["groups"]
            result = groups.find_one(
                {"_id": ObjectId(group_id)}, {"_id": 1})

            return json_util.dumps(result)

    def get_groups(self):
        """
        Return all the groups values in the database,
        NOT recommand to use as it is slown

        Returns:
            _type_: _description_
        """
        LOGGER.info("Get groups")
        with self._establish_connection() as client:
            db = client[DB_NAME]
            groups_collection = db.groups
            result = groups_collection.find()

            return json_util.dumps(result)

    def get_group_records(self, group_id, includ_image=False):
        LOGGER.info("Get group records")
        with self._establish_connection() as client:
            db = client[DB_NAME]
            groups_collection = db.groups

            projection = {"records": 1}
            if not includ_image:
                del projection["records"]
                projection["records.base64"] = 0
                projection["records.hash"] = 0

            return groups_collection.find_one(
                {"_id": ObjectId(group_id)}, projection)

    def get_groups_info(self):
        LOGGER.info("Get groups info")
        with self._establish_connection() as client:
            db = client[DB_NAME]
            groups_collection = db.groups

            result = groups_collection.find({}, {"name": 1, "users": 1, "_id": 1}).sort(
                [('group_number', pymongo.ASCENDING)])

            return json_util.dumps(result)

    # PENDING RELATED
    def get_pending_queue(self, request_id):
        LOGGER.info("Get pending queue.")
        with self._establish_connection() as client:
            db = client[DB_NAME]
            parse_queue = db["pending_queue"]
            result = parse_queue.find_one(
                {"request_id": request_id}, {"request_id": 1, "_id": 0})

            return json_util.dumps(result)

    def insert_pending_queue(self, request_id):
        LOGGER.info("Insert pending queue.")
        with self._establish_connection() as client:
            db = client[DB_NAME]
            pending_queue = db["pending_queue"]

            pending_queue_id = self._get_pending_queue_object_id()
            pending_queue.update_one(
                pending_queue_id, {"$push": {"request_id": request_id}})

    def delete_pending_queue(self, request_id):
        with self._establish_connection() as client:
            db = client[DB_NAME]
            pending_queue = db["pending_queue"]
            pending_queue_object_id = self._get_pending_queue_object_id()
            result = pending_queue.update_one(pending_queue_object_id, {
                "$pull": {"request_id": request_id}})

            # Check the result of the update
            if result.modified_count <= 0:
                LOGGER.error("Faile to add record into Database.")
                return False
            return True

    # USER RELATED
    def get_users_by_group_id(self, group_id):
        with self._establish_connection() as client:
            db = client[DB_NAME]
            groups_collection = db.groups

            result = groups_collection.find_one(
                {"_id": ObjectId(group_id)}, {"users": 1})

            return json_util.dumps(result)

    def insert_users(self, group_id, users: list):
        try:
            with self._establish_connection() as client:
                db = client[DB_NAME]
                groups = db["groups"]

                result = groups.update_one(
                    {"_id": ObjectId(group_id)}, {"$addToSet": {"users": {"$each": users}}})

                # Check the result of the update
                if result.modified_count <= 0:
                    LOGGER.info("No users added.")
                    return False
            return True

        except pymongo.errors.PyMongoError as e:
            LOGGER.error(
                "An error occurred when inserting new members: {}".format(str(e)))
            return False
