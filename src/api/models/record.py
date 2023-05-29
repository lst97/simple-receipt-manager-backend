from mongoengine import Document, fields


class Records(Document):
    hash = fields.StringField(required=True)
    base64 = fields.StringField(required=True)
    receipt = fields.ObjectIdField(required=False)
    __v = fields.IntField(db_field="__v")

    def __repr__(self):
        return f"<Record {self.id}>"

    def serialize(self):
        return {
            "hash": self.hash,
            "base64": self.base64,
            "receipt": str(self.receipt)
        }
