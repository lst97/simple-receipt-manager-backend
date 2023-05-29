import datetime
from models.user import User
from repositories.repository_factory import RepositoryFactory
from helpers.mongodb_helper import connect_to_mongodb
from mongoengine import DoesNotExist


class UserRepository(RepositoryFactory):

    def __init__(self):
        connect_to_mongodb()

    def create(self, user):
        # check if user exists
        if User.objects(email=user["email"]).first():
            
            return None

        # Create a new user document
        new_user = User(
            name=user["name"],
            email=user["email"],
            password=user["password"],
            create_date=user["create_date"],
            modified_date=user["modified_date"]
        )
        new_user.save()  # Save the user document to the database

        return new_user.serialize()

    def read(self, id):
        try:
            record = User.objects.get(id=id)
            return record
        except DoesNotExist:
            return None

    def readAll(self):
        users = User.objects.all()
        return [user.serialize() for user in users]

    def update(self, updated_user_data):
        # Update a user by ID
        try:
            user = User.objects(id=id)
            # Update the user document with the provided data
            user.name = updated_user_data.get("name", user.name)
            user.email = updated_user_data.get("email", user.email)
            user.password = updated_user_data.get("password", user.password)
            user.modified_date = datetime.now()  # Set modified_date to current time
            user.save()  # Save the updated user document
            return True
        
        except DoesNotExist:
            return None

    def delete(self, id):
        try:
            user = User.objects.get(id=id)
            user.delete()
            return True
        except DoesNotExist:
            return None
        