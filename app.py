from flask import Flask, request, abort
from flask_cors import CORS
from flask_restful import Resource, Api
from flask_json import FlaskJSON, json_response

from db import Neo4jService

app = Flask(__name__)

CORS(app)
FlaskJSON(app)

api = Api(app)

neo4j_service = Neo4jService()


@api.representation("application/json")
def output_json(data, code, headers=None):
    return json_response(data_=data, headers_=headers, status_=code)


class Authors(Resource):
    def get(self):
        name = request.args.get("query").lower()
        page = int(request.args.get("page"))
        size = int(request.args.get("size"))
        return neo4j_service.getAuthorsByQuery(name, page, size)


class Author(Resource):
    def get(self, id):
        response = neo4j_service.getAuthorById(id)
        if response:
            return response
        else:
            abort(400)


class Article(Resource):
    def get(self, id):
        response = neo4j_service.getArticleById(id)
        if response:
            return response
        else:
            abort(400)


class Coauthors(Resource):
    def get(self, id):
        response = neo4j_service.getCoauthorsById(id)
        return response


class MostRelevantAuthors(Resource):
    def post(self):
        response = {}

        topic = request.get_json()["topic"].lower()
        authorsNumber = request.get_json()["authorsNumber"]

        df = neo4j_service.getMostRelevantAuthorByTopic(topic, authorsNumber)

        response["affiliations"] = neo4j_service.getAffiliationsByAuthors(df.index.to_list())

        if "type" in request.get_json():
            filterType = request.get_json()["type"]
            filterAffiliations = request.get_json()["affiliations"]

            filteredAuthors = neo4j_service.getAuthorsByAffiliationFilters(
                filterType, filterAffiliations, df.index.to_list()
            )

            response = {**response, **neo4j_service.getCommunity(filteredAuthors)}

            return response

        else:
            response = {**response, **neo4j_service.getCommunity(df.index.to_list())}

            for index, weight in enumerate(df.values):
                response["nodes"][index]["weight"] = weight

            return response


class MostRelevantArticles(Resource):
    def post(self):
        response = {}

        topic = request.get_json()["topic"].lower()
        page = request.get_json()["page"]
        size = request.get_json()["size"]

        df = neo4j_service.getMostRelevantArticlesByTopic(topic)

        response["years"] = neo4j_service.getYearsByArticles(df.index.to_list())

        if "type" in request.get_json():
            filterType = request.get_json()["type"]
            filterYears = request.get_json()["years"]
            filteredArticles = neo4j_service.getArticlesByFilterYears(
                filterType, filterYears, df.index.to_list()
            )
            response = {**response, **neo4j_service.getArticlesByIds(filteredArticles, page, size)}
        else:
            response = {**response, **neo4j_service.getArticlesByIds(df.index.to_list(), page, size)}

        return response


class RandomAuthors(Resource):
    def get(self):
        return neo4j_service.getRandomAuthors()


class RandomTopics(Resource):
    def get(self):
        return neo4j_service.getRandomTopics()


class UpdateAuthorField(Resource):
    def post(self):
        data = request.get_json()
        author_id = data.get("author_id")
        field_name = data.get("field_name")
        new_value = data.get("new_value")

        if not all([author_id, field_name, new_value]):
            return {'message': "All fields are required: author_id, field_name, new_value"}

        return neo4j_service.updateAuthorField(field_name=field_name, id=author_id, new_value=new_value)


api.add_resource(Authors, "/authors/get-authors-by-query")
api.add_resource(MostRelevantAuthors, "/coauthors/most-relevant-authors")
api.add_resource(Author, "/author/<string:id>")
api.add_resource(Article, "/article/<string:id>")
api.add_resource(Coauthors, "/coauthors/<string:id>")
api.add_resource(MostRelevantArticles, "/articles/most-relevant-articles")
api.add_resource(RandomAuthors, "/random-authors")
api.add_resource(RandomTopics, "/random-topics")
api.add_resource(UpdateAuthorField, "/update-author-field/")
