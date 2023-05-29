from .srm_db import MongoDB
from .controllers.group_controller import group_controller_bp
from .controllers.receipt_controller import receipt_controller_bp

# Standard Library imports
import os
import io
import re
import base64
import json
import logging
import threading
from .helpers.mongodb_helper import MongoDBHelper
from flasgger import Swagger

from concurrent.futures import ThreadPoolExecutor

# Third-Party Library imports
import requests
from PIL import Image
import imagehash
from bs4 import BeautifulSoup as BSHTML
import subprocess

# Framework imports
from flask import Flask, request, jsonify, escape
from flask_cors import CORS

# Local imports
import bleach

# Dotenv imports
from dotenv import load_dotenv

LOGGER = logging.getLogger(__name__)
HOST_IP = 'localhost'
HOST_PORT = 5000

IMG_FOLDER = 'receipt_parser/data/img'
TEMP_FOLDER = 'receipt_parser/data/tmp'
OCR_FOLDER = 'receipt_parser/data/txt'

UUID_REGEX = '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
FILE_NAME_REGEX = '^[A-Za-z0-9_.-]+\.(jpg|jpeg|png)$'

API_PREFIX = os.environ.get('SRM_API_PREFIX')

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'config/.env'))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'this is a secret key'
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 MB

app.register_blueprint(
    group_controller_bp, url_prefix=API_PREFIX)

app.register_blueprint(
    receipt_controller_bp, url_prefix=API_PREFIX)

swagger = Swagger(app)

CORS(app)

# To be remove, replaced by MongoDBHelper
DB = MongoDB()

MongoDBHelper.connect_to_mongodb()


def execute_receipt_parser(files_name):
    """
    Moved to ParseRequestHandler class.
    Executes the receipt parser script as a separate thread, and
    calls the provided on_exit callback when the script exits.
    """

    def receipt_parser():
        """
        Thread function that runs the receipt parser script and captures its output.
        """
        LOGGER.info("Create Receipt Parser subprocess.")
        try:
            subprocess_command = ["python3",
                                  "./src/api/receipt_parser/receipt_parser.py"]
            subprocess_command.append(str(len(files_name)))
            for file_name in files_name:
                subprocess_command.append(file_name)

            parser_output_string = subprocess.check_output(
                subprocess_command, encoding='utf-8')

            return parser_output_string

        except (OSError, subprocess.CalledProcessError) as exception:
            LOGGER.error('Exception occured: ' + str(exception))
            return False

    with ThreadPoolExecutor() as executor:
        future = executor.submit(receipt_parser)
        return future.result()


# @app.route('/test/groups', methods=['POST', 'GET'])
# def groups():
#     if request.method == "GET":
#         return DB.get_groups()


@app.route('/test/group_records/<string:group_id>', methods=['GET'])
def group_records(group_id):
    """
    DEPRECATED replaced with get_groups() in GroupController
    """
    if request.method != "GET":
        return jsonify({'error': 'Invalid request method'}), 400

    # Find the group with the matching id and only return the "records" field
    group = DB.get_group_records(group_id)

    # Initialize an empty list for response
    response = []

    # Iterate through the records
    for record in group["records"]:
        record_obj = {
            "merchant_name": record["receipt"]["merchant_name"],
            "receipt_no": record["receipt"]["receipt_no"],
            "date": record["receipt"]["date"],
            "payer": record["receipt"]["payer"],
            "total": record["receipt"]["total"],
            "payment_method": record["receipt"]["payment_method"],
            "share_with": record["receipt"]["share_with"],
            "payment_status": record["receipt"]["payment_status"]
        }
        # Append the record object to the response list
        response.append(record_obj)

    return jsonify(response)


@app.route('/test/groups_info', methods=['GET'])
def groups_info():
    """
    Not used anymore, replaced with get_groups() in GroupController
    """
    return DB.get_groups_info()


@app.route('/test/<group>/receipts', methods=['POST', 'GET'])
def receipts():
    return "TODO"


@app.route('/test/<group>/recipts/<string:id>', methods=['POST', 'GET'])
def recipt(id):
    return "TODO"


UPLOAD_REQUEST_LOCK = threading.Lock()

# REFACTOR vvvvvvvv


class UploadRequests(object):
    """
    This class is used to manage the upload requests.
    Now it is DEPRECATED and replaced by ParseRequestHandler class.
    """
    pool = []
    invalid_requests_pool = []
    image_hashs = []
    pending_pool = {}  # currently not used.

    def __init__(self) -> None:
        pass

    def _is_exist(self, request_id):
        for request_obj in self.pool:
            if request_obj.request["request_id"] == request_id:
                return True

        return False

    def create(self, request_id,  group_id, total_files):
        if self.get_request(request_id) is None:
            self.pool.append(self.Request(
                self, request_id,  group_id, total_files))
        return self.pool[-1]

    class Request(object):
        def __init__(self, upload_requests_instance, request_id, group_id, total_files) -> None:
            self.upload_requests = upload_requests_instance
            self.request = {"request_id": request_id}
            self._initialize_values(group_id, total_files)

        def values(self):
            return self.request

        def _initialize_values(self, group_id, total_files):
            self.request["group_id"] = group_id
            self.request["total_files"] = total_files
            self.request["remaining"] = total_files
            self.request["files"] = []

        def insert_file(self, file_name, image_base64, image_hash):
            self.request["files"].append(
                {"name": file_name, "base64": image_base64, "hash": image_hash})

        def recived(self):
            self.request["remaining"] -= 1

        def remaining_files(self):
            return self.request["remaining"]

        def get_files(self):
            return self.request["files"]

        def get_files_name(self):
            files_name = []
            for image_file in self.request["files"]:
                files_name.append(image_file["name"])

            return files_name

        def update_receipts(self, receipts):
            """Inser receipts to each files and update receipt field

            Args:
                request_id (_type_): _description_
                receipts (_type_): _description_
                groups_info (_type_): _description_
            """
            # create a dictionary mapping file names to receipts
            receipt_dict = {r['file_name']: r for r in receipts}
            for file_idx, image_file in enumerate(self.request["files"]):
                if image_file["name"] in receipt_dict:
                    self.request["files"][file_idx]["receipt"] = receipt_dict[image_file["name"]]
                    self.request["files"][file_idx]["receipt"]["payer"] = ""
                    self.request["files"][file_idx]["receipt"]["share_with"] = []
                    self.request["files"][file_idx]["receipt"]["payment_status"] = 'false'
                    del receipt_dict[image_file["name"]]

        def update_users(self, group_info):
            self.request["users"] = group_info["users"]

    def get_request(self, request_id):
        for request_obj in self.pool:
            if request_obj.request["request_id"] == request_id:
                return request_obj
        return None

    def get_pending_request(self, request_id):
        for request_id, request_obj in self.pending_pool.items():
            if request_obj["request_id"] == request_id:
                return request_obj
        return None

    def to_pending_pool(self, request_id):
        self.pending_pool[request_id] = self.get_request(request_id).request
        threading.Thread(target=DB.insert_pending_queue,
                         args=(request_id,)).start()

        return self.pending_pool[request_id].copy()

    def remove(self, request_id):
        for idx, request_obj in enumerate(self.pool):
            if request_obj.request["request_id"] == request_id:
                del self.pool[idx]
                return True
        return False

    def remove_pending(self, request_id):
        for request_id, request_obj in self.pending_pool.items():
            if request_obj["request_id"] == request_id:
                del self.pending_pool[request_id]
                return True
        return False

    def drop(self, request_id):
        self.invalid_requests_pool.append(request_id)
        self.remove(request_id)

    def get_invalid_request(self, request_id):
        for invalid_requests_pool in self.invalid_requests_pool:
            if invalid_requests_pool == request_id:
                return True
        return False

    def is_valid_request(self, request_id):
        return False if self.get_invalid_request(request_id) is True else True

    @staticmethod
    def remove_base64(upload_request):
        upload_request = upload_request.request.copy()
        upload_request["files"] = [
            {"hash": image_file["hash"], "receipt": image_file["receipt"]} for image_file in upload_request["files"]]
        return upload_request


upload_requests = UploadRequests()


def validate_upload_request(request_id, groups_info, group_id, total_files, file_name, image_file):
    """ 
    DEPRECATED replaced with ImageUploadValidator.validate(request_id, pagination: json, file_name, image_file):
    """
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

    group_info = next(
        (group_info for group_info in groups_info if group_info["_id"]["$oid"] == group_id), None)
    if not group_info:
        return "Invalid group id."

    return ""


@app.route('/test/upload/<string:group_id>', methods=['POST'])
def handle_upload(group_id):
    """ 
    DEPRECATED replaced with GroupController.handle_image_upload(group_id:str)
    """
    # how many files are expected to be uploaded for this request_id
    request_id = request.form.get('request_id')
    total_files = request.form.get('total_files')
    image_file = request.files.get("file")
    if not image_file:
        return jsonify({"message": "No file is selected"}), 400
    image_bytes = image_file.read()

    groups_info = json.loads(DB.get_groups_info())
    error_message = validate_upload_request(
        request_id, groups_info, group_id, total_files, image_file.filename, image_bytes)
    if error_message != "":
        upload_requests.drop(request_id)
        LOGGER.warning(error_message)
        return jsonify({"message": error_message}), 400

    upload_request = upload_requests.create(
        request_id, group_id, int(total_files))

    # MUST BE TRUE
    group_info = next(
        (group_info for group_info in groups_info if group_info["_id"]["$oid"] == group_id), None)

    image = Image.open(io.BytesIO(image_bytes))
    image_hash = str(imagehash.average_hash(image))
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    upload_request.insert_file(image_file.filename, image_base64, image_hash)

    # save image file to disk
    try:
        base_path = os.path.join(os.path.dirname(
            __file__), 'receipt_parser/data/img', image_file.filename)
        fullpath = os.path.normpath(base_path)
        if not fullpath.startswith(base_path):
            raise Exception("Security Exception.")
        with open(fullpath, "wb") as stream:
            stream.write(base64.b64decode(image_base64))
    except Exception as e:
        LOGGER.error(e)
        upload_requests.drop(request_id)
        return jsonify({"message": "Server internal error, please try to upload it again."}), 500

    upload_request.recived()

    if upload_request.remaining_files() - 1 == 0:
        # current still sequenize, but plan to do it async later.
        files_name = upload_request.get_files_name()
        parser_output_string = execute_receipt_parser(files_name)
        receipts_json_string = parser_output_string.splitlines()[-1]
        receipts = json.loads(receipts_json_string)

        upload_request.update_receipts(receipts)
        upload_request.update_users(group_info)
        response = upload_requests.to_pending_pool(request_id)
        upload_requests.remove(request_id)

        response = upload_requests.remove_base64(upload_request)
        return jsonify(response)

    return jsonify({"message": "Received", "file_name": escape(image_file.filename)})

# TODO 28 May 2023: Refactor this class


class Submit:
    def insert_new_members_if_needed(self, group_id, users):
        users = [user for user in users if user]
        DB.insert_users(group_id, users)

    def get_members(self, user_request):
        users = []
        for record in user_request["files"]:
            users.append(record['receipt']["payer"])
            users += record['receipt']["share_with"]
        return list(set(users))

    def remove_pending_request(self, request_id):
        upload_requests.remove_pending(request_id)
        DB.delete_pending_queue(request_id)

    def update_records_with_base64(self, user_request):
        records = user_request["files"]
        for i, _ in enumerate(records):
            records[i]["base64"] = upload_requests.get_pending_request(
                user_request["request_id"])["files"][i]["base64"]
        user_request["files"] = records
        return user_request

    def validate(self, user_request):
        pending_queue = DB.get_pending_queue(user_request["request_id"])
        group_records = DB.get_group_records(user_request["group_id"])

        if not pending_queue or pending_queue == "null":
            return "Invalid request id."

        if not group_records or group_records == "null":
            return "Invalid group id."

        return ""


@ app.route('/test/submit', methods=['POST'])
def handle_submit():
    submit = Submit()

    user_request = request.json

    error_message = submit.validate(user_request)
    if error_message:
        return jsonify({"message": error_message}), 400

    cleaned_user_request = json.loads(bleach.clean(
        json.dumps(user_request), tags=[], attributes={}))
    response_message = "Process complete."
    if cleaned_user_request != user_request:
        response_message = "Process complete with warning: HTML tags were removed from your request for security reasons."

    users = submit.get_members(cleaned_user_request)
    submit.insert_new_members_if_needed(
        cleaned_user_request["group_id"], users)

    cleaned_user_request = submit.update_records_with_base64(
        cleaned_user_request)

    DB.insert_upload_receipts(cleaned_user_request)
    submit.remove_pending_request(cleaned_user_request["request_id"])

    return jsonify({"message": response_message}), 200


@ app.route('/test/group_info/<string:group_id>', methods=['GET'])
def handle_group_info(group_id):
    """
    DEPRECATED
    """
    return DB.get_group_info(group_id), 200

# TODO 28 May 2023: Move to a new controller file


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
