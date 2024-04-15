import json
import xml.etree.ElementTree as ET

from utils.request_http import HttpRequest


class RequestElSevierService:
    def __init__(self):
        self.http_request = HttpRequest("https://api.elsevier.com/content/")

    def get_author_information(self, id: str):
        try:
            route = f"author/author_id/{id}"
            response = self.http_request.do_get(route)
            return response
        except Exception as e:
            raise Exception("Error on get_author_information", str(e))

    @staticmethod
    def convert_xml_to_json(xml: str):
        try:
            root = ET.fromstring(xml)
            data = {}
            for child in root:
                if child.tag == 'coredata':
                    for subchild in child:
                        data[subchild.tag] = subchild.text
            return data
        except Exception as e:
            raise Exception("Error on convert_xml_to_json", str(e))

    @staticmethod
    def get_author_articles_count(data: dict):
        return data.get("document-count")
