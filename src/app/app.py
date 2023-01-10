from flask import Flask, request
import pymongo

app = Flask(__name__)


def establish_connection():
    # Connect to the MongoDB server
    client = pymongo.MongoClient("mongodb://localhost:27017/")

    # Select the database
    return client["simple_recipt_manager"]


@app.route('/groups', methods=['POST', 'GET'])
def groups():
    if request.method == "GET":

        db = establish_connection()

        # Show all collections in the database
        group_name = db.list_collection_names()
        return group_name


@app.route('/<group>/records', methods=['POST', 'GET'])
def groups():
    if request.method == "GET":

        return "TODO"


@app.route('/<group>/recipt/<id>', methods=['POST', 'GET'])
def groups():
    if request.method == "GET":

        db = establish_connection()

        return "TODO"


if __name__ == '__main__':
    app.run(debug=True)
