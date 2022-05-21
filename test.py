"""from bs4 import BeautifulSoup

PagePath = 'page_test.html'

parsed_page = None

with open(PagePath) as file:
    parsed_page = BeautifulSoup(file, 'html.parser')

print(parsed_page.body.find_all())"""


import urllib3
from bs4 import BeautifulSoup
poolManager = urllib3.PoolManager()
req = poolManager.request('GET', 'https://theobject.ru/')
#bf = BeautifulSoup(, 'html.parser')
with open('page.html', 'w') as file:
    file.write((req.data).decode('utf-8'))