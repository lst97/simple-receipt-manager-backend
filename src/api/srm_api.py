from flask import Flask, request
import pymongo
from flask_cors import CORS
import json
from bson import json_util, ObjectId
from dotenv import load_dotenv
import os
from os.path import join, dirname
import logging
import subprocess
import threading
import requests
from bs4 import BeautifulSoup as BSHTML
import base64

load_dotenv(dotenv_path=join(dirname(__file__), 'config/.env'))
app = Flask(__name__)
app.config['SECRET_KEY'] = 'this is a secret key'
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 MB

CORS(app)

LOGGER = logging.getLogger(__name__)
HOST_IP = 'localhost'
HOST_PORT = 5000


def on_exit():
    LOGGER.info("on_exit() callback EXECUTED.")


def execute_receipt_parser():
    def receipt_parser_thread(on_exit):
        LOGGER.info("Create Receipt Parser subprocess.")
        try:
            console_output = subprocess.run(
                ["python3", "./src/api/receipt_parser/receipt_parser.py"], capture_output=False)

            LOGGER.info(console_output.stdout)
        except (OSError, subprocess.CalledProcessError) as exception:
            LOGGER.error('Exception occured: ' + str(exception))
            LOGGER.info('Receipt Parser failed to complete it execution.')
            return False
        else:
            # notify API to find the result in data/txt
            on_exit()

        return True

    parser_thread = threading.Thread(
        target=receipt_parser_thread, args=(on_exit,))
    parser_thread.start()

    return parser_thread


def establish_connection():
    # Connect to the MongoDB server
    client = pymongo.MongoClient(
        "mongodb+srv://{0}:{1}@{2}/test".format(os.getenv('ADMIN_NAME'), os.getenv('ADMIN_PASSWORD'), os.getenv('DB_CONNECTION_STRING')))

    # Select the database
    return client["simple-receipt-manager"]


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


@app.route('/<group>/recipts/<string:id>', methods=['POST', 'GET'])
def recipt(id):
    if request.method == "GET":

        db = establish_connection()

        return "TODO"

# For testing


upload_requests = {"records": []}


def search_upload_requests(request_id):
    idx = 0
    for record in upload_requests["records"]:
        if record["request_id"] == request_id:
            return idx
        idx += 1
    return -1


@app.route('/test/upload', methods=['POST'])
def handle_upload():
    # how much file expected to be upload for this request_id
    total_files = int(request.form.get('total_files'))
    request_id = request.form.get('request_id')
    image_file = request.files.get("file")
    image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    record_index = search_upload_requests(request_id)
    if record_index == -1:
        upload_requests["records"].append(
            {"request_id": request_id, "total_files": total_files, "remaining": total_files, "files": {"file_name": image_file.filename, "base64": image_base64}})

    upload_requests["records"][record_index]["remaining"] -= 1
    try:
        with open(join(dirname(__file__), 'receipt_parser/data/img/{0}'.format(image_file.filename)), "wb") as stream:
            stream.write(base64.b64decode(image_base64))
    except Exception as e:
        LOGGER.error(e)

    # TODO: Insert Parsed Data to DB.
    # Delete Parsed Files.
    if upload_requests["records"][record_index]["remaining"] == 0:
        # delete the upload_requests with this request_id
        execute_receipt_parser()
        return json.dumps({"response": "execute_receipt_parser()"}, default=json_util)

    return json.dumps({"response": {"request_id": request_id, "total_files": total_files, "remaining": total_files, "files": {"file_name": image_file.filename, "base64": image_base64}}}, default=json_util)


@app.route('/test/parse/<string:request_id>', methods=['GET'])
def parse_receipt(request_id):
    if request.method == "GET":
        # execute_receipt_parser()
        db = establish_connection()
        parse_queue_collection = db.parse_queue
        cursor = parse_queue_collection.find({"request_id": request_id})
        response = []
        for doc in cursor:
            response.append(doc)
        return json.dumps(response, default=json_util.default)

# For Testing


# @app.route('test/upload/parse', methods=['GET'])
# def parse_receipt():
#     if request.method == "GET":

#         execute_receipt_parser()
#         # db = establish_connection()

#         return "TODO"

# # use external API


@app.route('/external/abn/search', methods=['GET'])
def abn_query():
    if request.method == "GET":
        arg = request.args.get('id')
        if arg != "":
            resp = requests.get('{0}?id={1}'.format(
                os.getenv('ABN_DATA_API_URL'), arg))

            resp_html = resp.text
            soup = BSHTML(resp_html, 'html.parser')

            merchant_name = {"merchant_name": ""}
            if len(soup.find_all(alt="error")) == 0 and len(soup.find_all(alt="Error")) == 0:
                merchant_name["merchant_name"] = soup.find_all(
                    itemprop="legalName")[0].string

            return json.dumps(merchant_name, default=json_util.default)


def run():
    app.run(host=HOST_IP, debug=False)
