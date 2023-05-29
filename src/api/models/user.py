from mongoengine import Document, fields


class Users(Document):
    name = fields.StringField(required=True)
    email = fields.EmailField(required=True)
    password = fields.StringField(required=True)
    create_date = fields.DateTimeField()
    modified_date = fields.DateTimeField()
    __v = fields.IntField(db_field="__v")

    def __repr__(self):
        return f"<User {self.name}>"

    def serialize(self):
        return {
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "create_date": self.create_date,
            "modified_date": self.modified_date
        }
