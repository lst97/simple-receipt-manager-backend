import base64
from .srm_db import *
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
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
import re
import concurrent.futures


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

UUID_REGEX = '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
FILE_NAME_REGEX = '^[A-Za-z0-9_.-]+\.(jpg|jpeg|png|gif)$'


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


def execute_receipt_parser(files_name):
    """
    Executes the receipt parser script as a separate thread, and
    calls the provided on_exit callback when the script exits.
    """

    def receipt_parser():
        """
        Thread function that runs the receipt parser script and captures its output.
        """
        LOGGER.info("Create Receipt Parser subprocess.")
        try:
            LOGGER.info("Get files info from API")
            subprocess_command = ["python3",
                                  "./src/api/receipt_parser/receipt_parser.py"]
            subprocess_command.append(str(len(files_name)))
            for file_name in files_name:
                subprocess_command.append(file_name)

            parser_output_string = subprocess.check_output(
                subprocess_command, encoding='utf-8')

            on_exit()
            return parser_output_string

        except (OSError, subprocess.CalledProcessError) as exception:
            LOGGER.error('Exception occured: ' + str(exception))
            LOGGER.info('Receipt Parser failed to complete it execution.')
            return False

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(receipt_parser)
        return future.result()

    # parser_thread = threading.Thread(target=receipt_parser)
    # parser_thread.start()
    # parser_thread.join()
    # return parser_output_string


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


UPLOAD_REQUEST_LOCK = threading.Lock()


class UploadRequests():
    def __init__(self) -> None:
        self.pool = {}
        self.invalid_request_pool = []
        self.image_hashs = []
        self.pending_pool = {}
        pass

    def create(self, request_id):
        try:
            # ignore if request_id exsit.
            self.pool[request_id]
        except KeyError:
            with UPLOAD_REQUEST_LOCK:
                self.pool[request_id] = {
                    "group_id": "", "total_files": "", "remaining": "", "files": []}

    def initialize_values(self, request_id, group_id, total_files):
        if self.pool[request_id]["group_id"] == "":
            self.pool[request_id]["group_id"] = group_id

        if self.pool[request_id]["total_files"] == "":
            self.pool[request_id]["total_files"] = total_files
            self.pool[request_id]["remaining"] = total_files

    def insert_file(self, request_id, file_name, image_base64, image_hash):
        try:
            upload_request = self.pool[request_id]
        except KeyError:
            return None

        upload_request["files"].append(
            {"name": file_name, "base64": image_base64, "hash": image_hash})

    def recived(self, request_id):
        with UPLOAD_REQUEST_LOCK:
            self.pool[request_id]["remaining"] -= 1

    def mark_invalid(self, request_id):
        self.pool[request_id]["is_valid"] = False

    def drop(self, request_id):
        with UPLOAD_REQUEST_LOCK:
            self.invalid_request_pool.append(request_id)
            del self.pool[request_id]

    def is_valid_request(self, request_id):
        try:
            self.invalid_request_pool.index(request_id)
        except ValueError:
            try:
                self.pool[request_id]
                return True
            except KeyError:
                return False

        return False

    def find_request(self, request_id):
        try:
            return self.pool[request_id]
        except KeyError:
            return None

    def remaining_files(self, request_id):
        return self.pool[request_id]["remaining"]

    def find_image_hash(self, image_hash):
        try:
            return self.image_hashs.index(image_hash)
        except ValueError:
            return None

    def get_files(self, request_id):
        return self.pool[request_id]["files"]

    def get_files_name(self, request_id):
        files_name = []
        for image_file in self.pool[request_id]["files"]:
            files_name.append(image_file["name"])

        return files_name

    def pending(self, request_id):
        self.pending_pool.append(self.pool[request_id])

    def update_receipts(self, request_id, receipts):
        # create a dictionary mapping file names to receipts
        receipt_dict = {r['file_name']: r for r in receipts}
        for file_idx, image_file in enumerate(self.pool[request_id]["files"]):
            if image_file["name"] in receipt_dict:
                self.pool[request_id]["files"][file_idx]["receipt"] = receipt_dict[image_file["name"]]
                del receipt_dict[image_file["name"]]

    def get_pending_request(self, request_id):
        return self.pending_pool[request_id]

    def to_pending_pool(self, request_id):
        self.pending_pool[request_id] = self.pool[request_id]
        self.pending_pool["upload"] = False
        del self.pool[request_id]

    @staticmethod
    def remove_base64(upload_request):
        upload_request["files"] = [
            {"hash": image_file["hash"], "receipt": image_file["receipt"]} for image_file in upload_request["files"]]
        return upload_request


upload_requests = UploadRequests()


def validate_upload_request(request_id, group_id, total_files, file_name, image_file):

    if not (re.match(UUID_REGEX, request_id) and upload_requests.is_valid_request(request_id)):
        return "Invalid request id."

    if not re.match(FILE_NAME_REGEX, file_name):
        return "Invalid file name."

    try:
        total_files = int(total_files)
    except ValueError:
        return "Invalid total files number."
    try:
        Image.open(io.BytesIO(image_file))
    except IOError:
        return "Invalid file format."

    records = get_group_records(group_id)
    if records is None:
        return "Invalid group id."

    return ""


@app.route('/test/upload/<string:group_id>', methods=['POST'])
def handle_upload(group_id):

    # how many files are expected to be uploaded for this request_id
    request_id = request.form.get('request_id')
    upload_requests.create(request_id)
    total_files = request.form.get('total_files')

    image_file = request.files.get("file")
    image_bytes = image_file.read()

    error_message = validate_upload_request(
        request_id, group_id, total_files, image_file.filename, image_bytes)
    if error_message != "":
        upload_requests.drop(request_id)
        LOGGER.warning(error_message)
        return jsonify({"message": error_message}), 400

    upload_requests.initialize_values(request_id, group_id, int(total_files))
    image = Image.open(io.BytesIO(image_bytes))
    image_hash = str(imagehash.average_hash(image))
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    if upload_requests.find_image_hash(image_hash) is None:
        # file already in DB
        upload_requests.insert_file(
            request_id, image_file.filename, image_base64, image_hash)
        upload_requests.recived(request_id)
    else:
        upload_requests.recived(request_id)
        return jsonify("Duplicated image."), 400

    # save image file to disk
    try:
        with open(join(dirname(__file__), 'receipt_parser/data/img', image_file.filename), "wb") as stream:
            stream.write(base64.b64decode(image_base64))
    except Exception as e:
        LOGGER.error(e)
        upload_requests.drop(request_id)
        return jsonify({"message": "Server instenal error, please try to upload it again."}), 500

    if upload_requests.remaining_files(request_id) == 0:
        # current still sequenize, but plan to do it async later.
        files_name = upload_requests.get_files_name(request_id)
        parser_output_string = execute_receipt_parser(files_name)
        receipts_json_string = parser_output_string.splitlines()[-1]
        receipts = json.loads(receipts_json_string)

        upload_requests.update_receipts(request_id, receipts)
        upload_requests.to_pending_pool(request_id)

        response = upload_requests.get_pending_request(request_id)
        response = upload_requests.remove_base64(response)
        return jsonify(response)

    return jsonify({"message": "Received", "file": image_file.filename})


@ app.route('/internal/parse/<string:request_id>', methods=['GET', 'POST'])
def handle_parse(request_id):
    if request.method == "GET":
        # TODO: GET parse_queue_id from DB.

        return get_parse_queue(request_id)
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
