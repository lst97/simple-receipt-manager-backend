from .repository_factory import RepositoryFactory
from ..models.record import Records
from mongoengine import DoesNotExist


class RecordRepository(RepositoryFactory):
    def create(self, record_data):
        record = Records(
            hash=record_data["hash"],
            base64=record_data["base64"],
            receipt=record_data.get("receipt")
        )
        record.save()
        return str(record.id)

    def read(self, id):
        try:
            record = Records.objects.get(id=id)
            return record
        except DoesNotExist:
            return None

    def readAll(self):
        records = Records.objects()
        return records

    def update(self, id, updated_record_data):
        try:
            record = Records.objects.get(id=id)
            record.hash = updated_record_data.get("hash", record.hash)
            record.base64 = updated_record_data.get("base64", record.base64)
            record.receipt = updated_record_data.get("receipt", record.receipt)
            record.save()
            return True
        except DoesNotExist:
            return False

    def delete(self, id):
        try:
            record = Records.objects.get(id=id)
            record.delete()
            return True
        except DoesNotExist:
            return False
