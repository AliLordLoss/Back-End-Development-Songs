from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/health", methods=["GET"])
def get_health():
    return {"status": "OK"}, 200


@app.route("/count", methods=["GET"])
def get_count():
    """return length of data"""
    count = db.songs.count_documents({})

    return {"count": count}, 200


@app.route("/song", methods=["GET"])
def list_songs():
    return {"songs": parse_json(db.songs.find({}))}, 200


@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    song = db.songs.find_one({"id": id})
    if not song:
        return {"message": "song with id not found"}, 404
    return parse_json(song), 200


@app.route("/song", methods=["POST"])
def create_song():
    data = request.json
    id = data["id"]
    if db.songs.find_one({"id": id}):
        return {"Message": f"song with id {id} already present"}, 302
    insert_result = db.songs.insert_one(data)
    return {"inserted id": {"$oid": str(insert_result.inserted_id)}}, 201


@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    data = request.json

    if not db.songs.find_one({"id": id}):
        return {"message": "song not found"}, 404
    
    song = db.songs.update_one({"id": id}, {"$set": data})

    if song.modified_count > 0:
        return parse_json(db.songs.find_one({"id": id}))
    else:
        return {"message": "song found, but nothing updated"}


@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    result = db.songs.delete_one({"id": id})
    if result.deleted_count < 1:
        return {"message": "song not found"}, 404
    else:
        return "", 204
