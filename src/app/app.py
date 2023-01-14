from flask import Flask, request
import pymongo
from flask_cors import CORS
import json
from bson import json_util, ObjectId

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


@app.route('/group_records/<string:group_id>', methods=['GET'])
def group_records(group_id):
    if request.method == "GET":
        db = establish_connection()
        groups_collection = db.groups

        cursor = groups_collection.find(
            {"_id": ObjectId(group_id)}, {"records": 1})

        records = []
        for doc in cursor:
            records.append(doc)

        response = []
        for record in records[0]["records"]:
            record_obj = {}
            record_obj["merchant_name"] = record["receipts"][0]["merchant_name"]
            record_obj["receipt_no"] = record["receipts"][0]["receipt_no"]
            record_obj["date"] = record["receipts"][0]["date"]
            record_obj["payer"] = record["payer"]
            record_obj["total"] = record["receipts"][0]["total"]
            record_obj["payment_method"] = record["receipts"][0]["payment_method"]
            record_obj["share_with"] = record["share_with"]
            response.append(record_obj)

        return json.dumps(response, default=json_util.default)


@app.route('/groups_info', methods=['GET'])
def groups_info():
    if request.method == "GET":
        db = establish_connection()
        groups_collection = db.groups

        cursor = groups_collection.find({}, {"name": 1}).sort([
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
    app.run(debug=False)
