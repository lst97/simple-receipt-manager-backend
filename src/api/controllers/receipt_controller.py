import json
from bson import ObjectId
from flask import Blueprint

from ..repositories.receipt_repository import ReceiptRepository
from flask import jsonify
import os
from ..helpers.response_helper import ResponseHelper, ResponseType, ResponseMessage

API_PREFIX = os.environ.get('SRM_API_PREFIX')

receipt_controller_bp = Blueprint('receipts', __name__)


class ReceiptController:
    def __init__(self, receipt_repository) -> None:
        self.receipt_repository = receipt_repository

    def get_all_receipt(self):
        receipts = self.receipt_repository.readAll()
        if receipts is None:
            return {}
        return receipts

    def get_receipt(self, receipt_id):
        receipt = self.receipt_repository.read(receipt_id)
        if receipt is None:
            return {}
        return receipt

    def create_receipt(self):
        pass

    def update_receipt(self, receipt_id):
        pass

    def delete_receipt(self, receipt_id):
        pass


receipt_repository = ReceiptRepository()

receipt_controller = ReceiptController(receipt_repository)


@receipt_controller_bp.route("/receipts", methods=["GET"])
def get_all_receipt():
    return jsonify(ResponseHelper(ResponseType.SUCCESS, ResponseMessage.SUCCESS, receipt_controller.get_all_receipt()).to_json())


@receipt_controller_bp.route("/receipts/<string:receipt_id>", methods=["GET"])
def get_receipt(receipt_id):
    return jsonify(ResponseHelper(ResponseType.SUCCESS, ResponseMessage.SUCCESS, receipt_controller.get_receipt(receipt_id)).to_json())
