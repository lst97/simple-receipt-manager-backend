from flask import Flask, request
import pymongo
from flask_cors import CORS
import json
from bson import json_util

app = Flask(__name__)
CORS(app)


def establish_connection():
    # Connect to the MongoDB server
    client = pymongo.MongoClient("mongodb://localhost:27017/")

    # Select the database
    return client["simple_recipt_manager"]


@app.route('/groups', methods=['POST', 'GET'])
def groups():
    db = establish_connection()

    if request.method == "GET":
        groups_collection = db.groups

        # get all documents in the collection
        cursor = groups_collection.find()

        # convert cursor to JSON string
        return json.dumps(list(cursor), default=json_util.default)


@app.route('/groups_name', methods=['GET'])
def groups_name():
    if request.method == "GET":
        db = establish_connection()
        groups_collection = db.groups

        cursor = groups_collection.find({}, {"name": 1, "_id": 0}).sort([
            ('group_number', pymongo.ASCENDING)])

        return json.dumps(list(cursor), default=json_util.default)


@app.route('/<group>/receipts', methods=['POST', 'GET'])
def receipts():
    if request.method == "GET":

        return "TODO"


@app.route('/<group>/recipts/<id>', methods=['POST', 'GET'])
def recipt():
    if request.method == "GET":

        db = establish_connection()

        return "TODO"


if __name__ == '__main__':
    app.run(debug=True)
