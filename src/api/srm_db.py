import pymongo
from dotenv import load_dotenv
import os
from os.path import join, dirname


DB_NAME = "simple-receipt-manager"

load_dotenv(dotenv_path=join(dirname(__file__), 'config/.env'))


def establish_connection():
    # Connect to the MongoDB server
    client = pymongo.MongoClient(
        "mongodb+srv://{0}:{1}@{2}/test".format(os.getenv('ADMIN_NAME'), os.getenv('ADMIN_PASSWORD'), os.getenv('DB_CONNECTION_STRING')))

    # Select the database
    return client[DB_NAME]
