import pandas as pd

from utils.request_http import HttpRequest

http_client = HttpRequest('http://172.28.36.25:5000/')

response = http_client.do_get('/author/57193901649')

print(response.json())
