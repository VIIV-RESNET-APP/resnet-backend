from flask import Flask, request, abort
from flask_cors import CORS
from flask_restful import Resource, Api
from flask_json import FlaskJSON, json_response

from db import getAuthorsByQuery, getAuthorById, getArticleById

app = Flask(__name__)

CORS(app)
FlaskJSON(app)

api = Api(app)


@api.representation('application/json')
def output_json(data, code, headers=None):
    return json_response(data_=data, headers_=headers, status_=code)


class Authors(Resource):
    def get(self):
        name = request.args.get('query').lower()
        page = int(request.args.get('page'))
        size = int(request.args.get('size'))
        return getAuthorsByQuery(name, page, size)

class Author(Resource):
    def get(self, id):
        response = getAuthorById(id)
        if response:
            return response
        else:
            abort(400)


class Article(Resource):
    def get(self, id):
        response = getArticleById(id)
        if response:
            return response
        else:
            abort(400)



api.add_resource(Authors, '/authors/get-authors-by-query')
api.add_resource(Author, '/author/<string:id>')
api.add_resource(Article, '/article/<string:id>')
