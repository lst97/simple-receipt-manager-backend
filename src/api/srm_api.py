import base64
from .srm_db import *
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from bson import json_util
from dotenv import load_dotenv
import os
from os.path import join, dirname
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

IMG_FOLDER = 'receipt_parser/data/img'
TEMP_FOLDER = 'receipt_parser/data/tmp'
OCR_FOLDER = 'receipt_parser/data/txt'


def delete_parsed_data(files_name):
    for file_name in files_name:
        try:
            LOGGER.info("Delete parsed images in local storage.")
            os.remove(join(dirname(__file__), IMG_FOLDER, file_name))
            os.remove(join(dirname(__file__), TEMP_FOLDER, file_name))
            os.remove(join(dirname(__file__), OCR_FOLDER, file_name + '.txt'))
        except OSError as e:
            LOGGER.info(e)


def get_files_from_api(request_id):
    response = requests.get(
        '{0}/internal/parse/{1}'.format(os.getenv("SRM_API_URL"), request_id))

    files = []
    if response.status_code == 200:
        json_data = response.json()
        for files_obj in json_data["files"]:
            files.append(files_obj["file_name"])

    return files


def on_exit():
    LOGGER.info("on_exit() callback EXECUTED.")


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
    if request.method == "GET":
        return get_groups()


@app.route('/group_records/<string:group_id>', methods=['GET'])
def group_records(group_id):
    if request.method != "GET":
        return jsonify({'error': 'Invalid request method'}), 400

    # Find the group with the matching id and only return the "records" field
    group = get_group_records(group_id)

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

    return get_groups_info()


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


upload_requests = {}


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

    if find_image_hash(image_hash) is not None:
        LOGGER.info("Duplicated image found.")
        return jsonify({"message": "Duplicated image."})

    # convert image to base64
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    if request_id not in upload_requests:
        upload_requests[request_id] = {
            "request_id": request_id, "total_files": total_files, "remaining": total_files, "files": [], "hashs": []}

    upload_requests[request_id]["remaining"] -= 1

    # save image file to disk
    try:
        with open(join(dirname(__file__), f'receipt_parser/data/img/{image_file.filename}'), "wb") as stream:
            stream.write(base64.b64decode(image_base64))
    except Exception as e:
        LOGGER.error(e)

    # append the file name and base64 to the current record
    upload_requests[request_id]["files"].append({
        "file_name": image_file.filename,
        "base64": image_base64,
        "hash": image_hash})

    # if no remaining files, execute receipt parser
    if upload_requests[request_id]["remaining"] == 0:

        # add records to parse_queue db
        insert_parse_queue(
            upload_requests[request_id]["request_id"],
            group_id,
            upload_requests[request_id]["files"],
        )

        parser_thread = execute_receipt_parser(request_id)
        parser_thread.join()
        receipts_json_string = parser_output_string.splitlines()[-1]
        receipts = json.loads(receipts_json_string)

        for image_file in upload_requests[request_id]["files"]:
            for receipt in receipts:
                if image_file["file_name"] == receipt['file_name']:
                    insert_record_by_group_id(
                        receipt, group_id, request_id, receipt['file_name'], image_file["base64"], image_file['hash'])
                    break

        # delete local storage
        files_name = []
        for image_file in upload_requests[request_id]["files"]:
            files_name.append(image_file["file_name"])
        threading.Thread(target=delete_parsed_data, args=(files_name,)).start()

        # upload image hash to db
        image_hashs = []
        for image_file in upload_requests[request_id]["files"]:
            image_hashs.append(image_file["hash"])
        if insert_image_hash(image_hashs) is False:
            return jsonify({"message": "Fail to insert image hash."})

        delete_parse_queue(request_id)
        del upload_requests[request_id]

    LOGGER.info("Upload complete.")
    return jsonify({"request_id": request_id, "total_files": total_files, "remaining": total_files})


@ app.route('/internal/parse/<string:request_id>', methods=['GET', 'POST'])
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


@ app.route('/external/abn/search', methods=['GET'])
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
