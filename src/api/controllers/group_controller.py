from dotenv import load_dotenv
from time import sleep
import json
from bson import ObjectId
from flask import Blueprint
from ..handlers.parse_request_handler import ParseRequestHandler
from ..repositories.group_repository import GroupRepository
from ..repositories.record_repository import RecordRepository
from flask import request, jsonify
import os
from ..helpers.response_helper import ResponseHelper, ResponseType, ResponseMessage
from ..utils.validator import ImageUploadValidator

load_dotenv(os.path.join(os.path.dirname(
    os.path.dirname(__file__)), 'config/.env'))

API_PREFIX = os.environ.get('SRM_API_PREFIX')

group_controller_bp = Blueprint('groups', __name__)


class GroupController:
    def __init__(self, group_repository: GroupRepository) -> None:
        self.group_repository = group_repository
        self.parse_request_handler = ParseRequestHandler()

    def get_all_group(self):
        return self.group_repository.readAll()

    def get_group_records(self, group_id, optimized=False):
        if optimized is False:
            # fire 2 queries
            record_repository = RecordRepository()
            group = self.group_repository.read(group_id)
            if group:
                record_ids = [ObjectId(record) for record in group["records"]]
                record_values = [record_repository.read(
                    record).serialize() for record in record_ids]
                return record_values
            else:
                return []
        else:
            # fire 1 query (not recommended), not looks good
            pipeline = [
                {"$match": {"_id": group_id}},
                {"$lookup": {
                    "from": "records",
                    "localField": "records",
                    "foreignField": "_id",
                    "as": "records"
                }},
                {"$unwind": "$records"},
                {"$project": {
                    "_id": 0,
                    "value": "$records.value"
                }}
            ]
            group = group_repository.aggregate(pipeline)
            records = [record.value for record in group]

            return records

    def handle_image_upload(self, image, image_bytes, request_id, pagination):

        # STEP 4: handle request and process image
        self.parse_request_handler.handle_request(
            request_id, image.filename, image_bytes, pagination)

        # STEP 5: return response
        if pagination.get('page') == pagination.get('total'):
            # I dont want to create a websocket in frontend to listen to the response
            # instead I will block the request which the page is the last page
            # then return the parsed data, the frontend will only receive the parsed data
            # in the last page request.
            # The problem is if this request raise error, there is no way to recover
            while True:
                if self.parse_request_handler.is_all_pages_processed(request_id):
                    response = self.parse_request_handler.get_parsed_data(
                        request_id)

                    # return parsed receipts
                    return response
                sleep(1)

        return {}

    def handle_submit(self, group_id):
        # TODO: refactor 29 May 2023
        pass

    def get_group(self, group_id):
        # Logic for handling GET request to /users/<user_id>
        group = self.group_repository.get_user_by_id(group_id)
        # Process and return the user or appropriate response
        pass

    def create_group(self):
        # Logic for handling POST request to /users
        data = request.json
        # Validate and process the data
        user = self.group_repository.create_user(data)
        # Return the created user or appropriate response

    def update_group(self, group_id):
        # Logic for handling PUT request to /users/<user_id>
        data = request.json
        # Validate and process the data
        user = self.group_repository.update_user(group_id, data)
        # Return the updated user or appropriate response

    def delete_group(self, group_id):
        # Logic for handling DELETE request to /users/<user_id>
        user = self.group_repository.delete_user(group_id)
        # Return the deleted user or appropriate response


group_repository = GroupRepository()
group_controller = GroupController(group_repository)


@group_controller_bp.route('/groups', methods=['GET'])
def get_all_group():
    """
    Get all groups
    ---
    responses:
        200:
            description: Get all groups

            examples:
                application/json: {"data":[{"id":"6472af7b086d0d10ccc4928f","name":"ST Zita","records":["6472af7b086d0d10ccc49285"],"users":["6472af7a086d0d10ccc4926c"]},{"id":"6472af7b086d0d10ccc49290","name":"Deakin","records":["6472af7b086d0d10ccc49286"],"users":["6472af7a086d0d10ccc4926d"]},{"id":"6472af7b086d0d10ccc49291","name":"Glen Waverley","records":["6472af7b086d0d10ccc49287"],"users":["6472af7a086d0d10ccc4926e"]}],"message":"Success","meta_data":null,"pagination":null,"status_code":200}     
    """
    groups = group_controller.get_all_group()
    if groups is None:
        return jsonify(ResponseHelper(ResponseType.ERROR, "Invalid group ID.", {}).to_json()), 404

    return jsonify(ResponseHelper(ResponseType.SUCCESS, ResponseMessage.SUCCESS, groups).to_json()), 200


@group_controller_bp.route('/group/<string:group_id>/records', methods=['GET'])
def get_group_records(group_id):
    records = group_controller.get_group_records(group_id)
    return jsonify(ResponseHelper(ResponseType.SUCCESS, ResponseMessage.SUCCESS, records).to_json())


@group_controller_bp.route('/group/<string:group_id>/upload', methods=['POST'])
def handle_image_upload(group_id):
    # STEP 1: get image base64 string and pagination info
    # STEP 2: base64 decode to image bytes

    if group_repository.read(group_id) is None:
        return jsonify(ResponseHelper(ResponseType.ERROR, "Invalid group ID.", {}).to_json()), 400

    data = json.loads(request.form.get('data'))
    image = request.files.get('file')
    request_id = data.get('metadata').get('requestId')
    pagination = data.get('pagination')

    if not image:
        return jsonify(ResponseHelper(ResponseType.ERROR, "No image found", {}).to_json()), 400

    image_bytes = image.read()

    # STEP 3: validation
    if ImageUploadValidator.validate(request_id, pagination, image.filename, image_bytes) is False:
        return jsonify(ResponseHelper(ResponseType.ERROR, "Invalid image.", {}).to_json()), 400

    response = group_controller.handle_image_upload(
        image, image_bytes, request_id, pagination)

    if len(response) > 0:
        return jsonify(ResponseHelper(ResponseType.SUCCESS, ResponseMessage.SUCCESS, response).to_json()), 200

    # not final page
    return jsonify(ResponseHelper(ResponseType.SUCCESS, "Image uploaded successfully.", response).to_json()), 200


@group_controller_bp.route('/group/<string:group_id>/submit', methods=['GET'])
def handle_submit(group_id):
    if group_repository.read(group_id) is None:
        return jsonify(ResponseHelper(ResponseType.ERROR, "Invalid group ID.", {}).to_json()), 400

    return group_controller.handle_submit(group_id)

# TODO
# @app.route('/test/<group>/receipts', methods=['POST', 'GET'])
# def receipts():
#     return "TODO"


# @app.route('/test/<group>/recipts/<string:id>', methods=['POST', 'GET'])
# def recipt(id):
#     return "TODO"


# Deprecated from srm_db.py
# @app.route('/test/groups_info', methods=['GET'])
# def groups_info():
#     return DB.get_groups_info()
