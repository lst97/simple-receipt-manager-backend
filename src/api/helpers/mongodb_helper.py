from mongoengine import connect
import os
import logging


LOGGING = logging.getLogger(__name__)


class MongoDBHelper:
    @staticmethod
    def connect_to_mongodb():
        connection_str = os.environ.get(
            'LOCAL_DB_CONNECTION_STRING').split(':')
        host = connection_str[0]
        port = int(connection_str[1])
        db_name = os.environ.get('DB_NAME')

        try:
            connect(
                db=db_name,
                host=host,
                port=port,
                username=os.environ.get('DB_USERNAME'),
                password=os.environ.get('DB_PASSWORD')
            )
            LOGGING.info("Connected to MongoDB")
        except ConnectionError as e:
            LOGGING.error("Failed to connect to MongoDB:", str(e))
