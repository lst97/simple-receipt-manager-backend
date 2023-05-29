from ..repositories.repository_factory import RepositoryFactory
from ..models.receipt import Receipts
from mongoengine import DoesNotExist


class ReceiptRepository(RepositoryFactory):
    def create(self, receipt):
        new_receipt = Receipts(
            abn=receipt.get("abn"),
            date=receipt.get("date"),
            file_name=receipt["file_name"],
            merchant_name=receipt["merchant_name"],
            merchant_phone=receipt.get("merchant_phone"),
            payer=receipt["payer"],
            payment_method=receipt.get("payment_method"),
            payment_status=receipt["payment_status"],
            receipt_no=receipt.get("receipt_no"),
            share_with=receipt.get("share_with", []),
            time=receipt["time"],
            total=receipt["total"]
        )
        new_receipt.save()
        return str(new_receipt.id)

    def read(self, id):
        try:
            receipt = Receipts.objects.get(id=id)
            return receipt.serialize()
        except DoesNotExist:
            return None

    def readAll(self):
        try:
            receipts = Receipts.objects()
            return [receipt.serialize() for receipt in receipts]
        except DoesNotExist:
            return None

    def update(self, id, updated_receipt_data):
        try:
            receipt = Receipts.objects.get(id=id)
            receipt.abn = updated_receipt_data.get("abn", receipt.abn)
            receipt.date = updated_receipt_data.get("date", receipt.date)
            receipt.file_name = updated_receipt_data.get(
                "file_name", receipt.file_name)
            receipt.merchant_name = updated_receipt_data.get(
                "merchant_name", receipt.merchant_name)
            receipt.merchant_phone = updated_receipt_data.get(
                "merchant_phone", receipt.merchant_phone)
            receipt.payer = updated_receipt_data.get("payer", receipt.payer)
            receipt.payment_method = updated_receipt_data.get(
                "payment_method", receipt.payment_method)
            receipt.payment_status = updated_receipt_data.get(
                "payment_status", receipt.payment_status)
            receipt.receipt_no = updated_receipt_data.get(
                "receipt_no", receipt.receipt_no)
            receipt.share_with = updated_receipt_data.get(
                "share_with", receipt.share_with)
            receipt.time = updated_receipt_data.get("time", receipt.time)
            receipt.total = updated_receipt_data.get("total", receipt.total)
            receipt.save()
            return True
        except DoesNotExist:
            return False

    def delete(self, id):
        try:
            receipt = Receipts.objects.get(id=id)
            receipt.delete()
            return True
        except DoesNotExist:
            return False
