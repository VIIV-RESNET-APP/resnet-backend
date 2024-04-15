import requests


class HttpRequest:

    def __init__(self, url_base: str):
        self.url_base = url_base

    def create_headers(self):
        try:
            headers = {
                "X-ELS-APIKey": "27b4573814803b246abfac3615c505e0",
                "X-ELS-Insttoken": "330aca6833fdfff081a7bd4d1ed7392f"
            }
            return headers
        except Exception as e:
            raise Exception("Error on create headers", str(e))

    def do_get(self, route: str, *args, **kwargs):
        try:
            url = self.url_base + route
            response = requests.get(url=url, headers=self.create_headers())
            return response
        except Exception as e:
            print("Error on do get", str(e))
            raise e

    def do_post(self, route: str, data: str):
        try:
            url = self.url_base + route
            response = requests.post(url=url, data=data, headers=self.create_headers())
            return response
        except Exception as e:
            print("Error on do post", str(e))
            raise e
