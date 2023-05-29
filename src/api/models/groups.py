from mongoengine import Document, fields


class Groups(Document):
    name = fields.StringField(required=True)
    users = fields.ListField(
        fields.ObjectIdField(required=True), required=False)
    records = fields.ListField(
        fields.ObjectIdField(required=True), required=False)
    __v = fields.IntField(db_field="__v")

    def __repr__(self):
        return f"<Groups {self.id}>"

    def serialize(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "users": [str(user_id) for user_id in self.users],
            "records": [str(record_id) for record_id in self.records],
        }
