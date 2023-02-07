from flask import Flask, request
from flask_cors import CORS
from flask_restful import Resource, Api
from flask_json import FlaskJSON, json_response

from db import getAuthorsByName

app = Flask(__name__)

CORS(app)
FlaskJSON(app)

api = Api(app)


@api.representation('application/json')
def output_json(data, code, headers=None):
    return json_response(data_=data, headers_=headers, status_=code)


class Author(Resource):
    def get(self):
        name = request.args.get('name').lower()
        page = int(request.args.get('page'))
        size = int(request.args.get('size'))
        return getAuthorsByName(name, page, size)


api.add_resource(Author, '/author/get-authors-by-name')