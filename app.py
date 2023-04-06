from flask import Flask, request, abort
from flask_cors import CORS
from flask_restful import Resource, Api
from flask_json import FlaskJSON, json_response

from db import getAuthorsByQuery, getAuthorById, getArticleById, getCoauthorsById, getCommunity, getMostRelevantAuthorByTopic, getAffiliationsByAuthors, getAuthorsByAffiliationFilters, getMostRelevantArticlesByTopic, getArticlesByIds, getYearsByArticles, getArticlesByFilterYears

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


class Coauthors(Resource):
    def get(self, id):
        response = getCoauthorsById(id)
        return response


class MostRelevantAuthors(Resource):
    def post(self):

        response = {}

        topic = request.get_json()['topic'].lower()
        authorsNumber = request.get_json()['authorsNumber']

        df = getMostRelevantAuthorByTopic(topic, authorsNumber)

        response['affiliations'] = getAffiliationsByAuthors(df.index.to_list())

        if 'type' in request.get_json():

            filterType = request.get_json()['type']
            filterAffiliations = request.get_json()['affiliations']

            filteredAuthors = getAuthorsByAffiliationFilters(
                filterType, filterAffiliations, df.index.to_list())

            response = {**response, **getCommunity(filteredAuthors)}

            return response

        else:
            response = {**response, **getCommunity(df.index.to_list())}

            for index, weight in enumerate(df.values):
                response['nodes'][index]['weight'] = weight

            return response


class MostRelevantArticles(Resource):
    def post(self):

        response = {}

        topic = request.get_json()['topic'].lower()
        page = request.get_json()['page']
        size = request.get_json()['size']

        df = getMostRelevantArticlesByTopic(topic)

        response['years'] = getYearsByArticles(df.index.to_list())

        if 'type' in request.get_json():
            filterType = request.get_json()['type']
            filterYears = request.get_json()['years']
            filteredArticles = getArticlesByFilterYears(
                filterType, filterYears, df.index.to_list())
            response = {**response, **
                        getArticlesByIds(filteredArticles, page, size)}
        else:

            response = {**response, **
                        getArticlesByIds(df.index.to_list(), page, size)}

        return response


api.add_resource(Authors, '/authors/get-authors-by-query')
api.add_resource(MostRelevantAuthors, '/coauthors/most-relevant-authors')
api.add_resource(Author, '/author/<string:id>')
api.add_resource(Article, '/article/<string:id>')
api.add_resource(Coauthors, '/coauthors/<string:id>')
api.add_resource(MostRelevantArticles, '/articles/most-relevant-articles')
