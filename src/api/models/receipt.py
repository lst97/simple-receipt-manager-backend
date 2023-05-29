from mongoengine import Document, fields


class Receipts(Document):
    abn = fields.StringField(required=False)
    date = fields.DateTimeField(required=False)
    file_name = fields.StringField(required=True)
    merchant_name = fields.StringField(required=True)
    merchant_phone = fields.StringField(required=False)
    payer = fields.ObjectIdField(required=True)
    payment_method = fields.StringField(required=False)
    payment_status = fields.StringField(required=True)
    receipt_no = fields.StringField(required=False)
    share_with = fields.ListField(
        fields.ObjectIdField(required=True), required=False)
    time = fields.DateTimeField(required=True)
    total = fields.DecimalField(required=True)
    __v = fields.IntField(db_field="__v")

    def __repr__(self):
        return f"<Receipt {self.id}>"

    def serialize(self):
        return {
            "abn": self.abn,
            "date": self.date,
            "file_name": self.file_name,
            "merchant_name": self.merchant_name,
            "merchant_phone": self.merchant_phone,
            "payer": str(self.payer),
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "receipt_no": self.receipt_no,
            "share_with": [str(person) for person in self.share_with],
            "time": self.time,
            "total": self.total
        }
