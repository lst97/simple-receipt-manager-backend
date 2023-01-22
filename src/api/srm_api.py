import base64
from .srm_db import establish_connection
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from bson import json_util, ObjectId
from dotenv import load_dotenv
import os
from os.path import join, dirname
import pymongo
import logging
import subprocess
import threading
import requests
from bs4 import BeautifulSoup as BSHTML
import imagehash
from PIL import Image
import io


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


def insert_parse_queue(request_id, group_id, files):
    db = establish_connection()
    parse_queue = db["parse_queue"]
    data = {
        "request_id": request_id,
        "group_id": group_id,
        "files":  files,
        "success": False
    }
    parse_queue.insert_one(data)


def delete_parse_queue(request_id):
    db = establish_connection()
    parse_queue_collection = db["parse_queue"]
    result = parse_queue_collection.find_one({"request_id": request_id})
    parse_queue_collection.delete_one(result)


def insert_image_hash(hash_str):
    db = establish_connection()
    parsed_images = db["parsed_images"]
    parsed_images_id = parsed_images.find_one({}, {"_id": 1})
    result = parsed_images.update_one(
        parsed_images_id, {"$push": {"hashs": hash_str}})

    # Check the result of the update
    if result.modified_count <= 0:
        LOGGER.error("Faile to add image hash into Database.")
        return False

    return True


def find_image_hash(hash_str):
    db = establish_connection()
    parsed_images = db["parsed_images"]
    cursor = parsed_images.find_one({"hashs": hash_str})
    return cursor or json_util.dumps(cursor)


def insert_record_by_group_id(receipt, group_id, request_id, file_name, image_base64):
    db = establish_connection()
    groups = db["groups"]
    record = {}
    record["receipts"] = receipt
    record["request_id"] = request_id
    record["file_name"] = file_name
    record["base64"] = image_base64
    record["raw"] = ""  # NEED OCR RAW TXT DATA

    result = groups.update_one(
        {"_id": ObjectId(group_id)}, {"$push": {"records": record}})

    # Check the result of the update
    if result.modified_count <= 0:
        LOGGER.error("Faile to add record into Database.")
        return False

    return True


def get_files_from_api(request_id):
    response = requests.get(
        '{0}/internal/parse/{1}'.format(os.getenv("SRM_API_URL"), request_id))

    files = []
    if response.status_code == 200:
        json_data = response.json()
        for files_obj in json_data["files"]:
            files.append(files_obj["file_name"])

    return files


parser_output_string = ""


def execute_receipt_parser(request_id) -> threading.Thread:
    """
    Executes the receipt parser script as a separate thread, and 
    calls the provided on_exit callback when the script exits.
    """
    def receipt_parser_thread():
        """
        Thread function that runs the receipt parser script and captures its output.
        """
        LOGGER.info("Create Receipt Parser subprocess.")
        try:
            LOGGER.info("Get files info from API")
            subprocess_command = ["python3",
                                  "./src/api/receipt_parser/receipt_parser.py"]
            files_name = get_files_from_api(request_id)
            subprocess_command.append(str(len(files_name)))
            for file_name in files_name:
                subprocess_command.append(file_name)

            global parser_output_string
            parser_output_string = subprocess.check_output(
                subprocess_command, encoding='utf-8')

        except (OSError, subprocess.CalledProcessError) as exception:
            LOGGER.error('Exception occured: ' + str(exception))
            LOGGER.info('Receipt Parser failed to complete it execution.')
            return False
        else:
            # notify API to find the result in data/txt
            on_exit()
        return True

    parser_thread = threading.Thread(target=receipt_parser_thread)
    parser_thread.start()
    return parser_thread


@app.route('/groups', methods=['POST', 'GET'])
def groups():
    db = establish_connection()

    if request.method == "GET":
        groups_collection = db.groups
        cursor = groups_collection.find()

        return json_util.dumps(cursor)


@app.route('/group_records/<string:group_id>', methods=['GET'])
def group_records(group_id):
    if request.method == "GET":
        db = establish_connection()
        groups_collection = db.groups

        # Find the group with the matching id and only return the "records" field
        group = groups_collection.find_one(
            {"_id": ObjectId(group_id)}, {"records": 1})

        # Initialize an empty list for response
        response = []

        # Iterate through the records
        for record in group["records"]:
            record_obj = {
                "merchant_name": record["receipts"][0]["merchant_name"],
                "receipt_no": record["receipts"][0]["receipt_no"],
                "date": record["receipts"][0]["date"],
                "payer": record["payer"],
                "total": record["receipts"][0]["total"],
                "payment_method": record["receipts"][0]["payment_method"],
                "share_with": record["share_with"]
            }
            # Append the record object to the response list
            response.append(record_obj)

        return jsonify(response)


@app.route('/groups_info', methods=['GET'])
def groups_info():
    if request.method != "GET":
        return jsonify({'error': 'Invalid request method'}), 400

    # Connect to the database
    db = establish_connection()
    groups_collection = db.groups

    # Retrieve the name of all groups, sorted by group_number
    cursor = groups_collection.find({}, {"name": 1}).sort(
        [('group_number', pymongo.ASCENDING)])

    # Convert the cursor to a list and serialize it as JSON

    return json_util.dumps(cursor)


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
    for i, record in enumerate(upload_requests["records"]):
        if record["request_id"] == request_id:
            return i
    return -1


@app.route('/test/upload/<string:group_id>', methods=['POST'])
def handle_upload(group_id):
    # how many files are expected to be uploaded for this request_id
    total_files = int(request.form.get('total_files'))
    request_id = request.form.get('request_id')
    image_file = request.files.get("file")

    # image hash
    image_bytes = image_file.read()
    image = Image.open(io.BytesIO(image_bytes))
    image_hash = str(imagehash.average_hash(image))

    # DEBUG COMMENTED
    # if find_image_hash(image_hash) is not None:
    #     return jsonify({"message": "Duplicated image."})

    # convert image to base64
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    # check if request_id already exists in upload_requests
    record_index = search_upload_requests(request_id)

    # if request_id does not exist, create a new record
    if record_index == -1:
        upload_requests["records"].append(
            {"request_id": request_id, "total_files": total_files, "remaining": total_files, "files": []})

        # set record_index to the last element
        record_index = len(upload_requests["records"]) - 1

    upload_requests["records"][record_index]["remaining"] -= 1

    # save image file to disk
    try:
        with open(join(dirname(__file__), f'receipt_parser/data/img/{image_file.filename}'), "wb") as stream:
            stream.write(base64.b64decode(image_base64))
    except Exception as e:
        LOGGER.error(e)

    # append the file name and base64 to the current record
    upload_requests["records"][record_index]["files"].append({
        "file_name": image_file.filename,
        "base64": image_base64
    })

    # upload image hash to db
    if insert_image_hash(image_hash) is False:
        # !!! user need to try the upload process again.
        return jsonify({"message": "Fail to insert image hash."})

    # if no remaining files, execute receipt parser
    if upload_requests["records"][record_index]["remaining"] == 0:

        # add records to parse_queue db
        insert_parse_queue(
            upload_requests["records"][record_index]["request_id"],
            group_id,
            upload_requests["records"][record_index]["files"],
        )

        # !!! protential thread safe issue
        # upload_requests["records"] = []

        parser_thread = execute_receipt_parser(request_id)
        parser_thread.join()
        receipts_json_string = parser_output_string.splitlines()[-1]
        receipts = json.loads(receipts_json_string)

        if len(receipts) != 0:
            for receipt in receipts:
                for record in upload_requests["records"]:
                    is_found = False
                    for image_file in record["files"]:
                        if image_file["file_name"] == receipt['file_name']:
                            image_base64 = image_file["base64"]
                            is_found = True
                            break
                    if is_found is True:
                        break

                insert_record_by_group_id(
                    receipt, group_id, request_id, receipt['file_name'], image_base64)
            pass
            # append base64 to receipts
            # upload to db base on the group id
        pass
        # TODO: delete the upload_requests with this request_id
        # TODO: add result to group
        # TODO: return receipts
    return jsonify({"request_id": request_id, "total_files": total_files, "remaining": total_files})


@app.route('/internal/parse/<string:request_id>', methods=['GET', 'POST'])
def handle_parse(request_id):
    if request.method == "GET":
        # TODO: GET parse_queue_id from DB.
        db = establish_connection()
        parse_queue = db["parse_queue"]
        cursor = parse_queue.find_one(
            {"request_id": request_id}, {"files": 1, "_id": 0})

        return json_util.dumps(cursor)
        # parse_queue_collection = db.parse_queue
        # cursor = parse_queue_collection.find({"request_id": request_id})
        # response = []
        # for doc in cursor:
        #     response.append(doc)
        # return json.dumps(response, default=json_util.default)

    if request.method == 'POST':
        pass
        # parse DONE
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
        # Get the 'id' parameter from the query string
        abn_id = request.args.get('id')
        # Check if the 'id' parameter is not empty
        if not abn_id:
            return json.dumps({'error': 'No ABN id provided'})

        # Make a GET request to the ABN Data API using the 'id' parameter
        resp = requests.get('{0}?id={1}'.format(
            os.getenv('ABN_DATA_API_URL'), abn_id))

        # Get the response text and parse it using BeautifulSoup
        resp_html = resp.text
        soup = BSHTML(resp_html, 'html.parser')

        # Initialize an empty merchant_name dictionary
        merchant_name = {"merchant_name": ""}
        # Check if the 'error' or 'Error' alt attribute is not found in the response
        if len(soup.find_all(alt="error")) == 0 and len(soup.find_all(alt="Error")) == 0:
            # Get the legalName element and store it in the merchant_name dictionary
            merchant_name["merchant_name"] = soup.find_all(
                itemprop="legalName")[0].string

        # Return the merchant_name dictionary as a JSON response
        return jsonify(merchant_name)


def run():
    app.run(host=HOST_IP, debug=False)
