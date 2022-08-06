import re
import sys
import time
import csv
from pprint import pprint
from datetime import datetime

import http.client
import logging

import requests
from bs4 import BeautifulSoup
from helper_functions import get_user_agent
# set user agent to imitate browser requests
user_agent: str = get_user_agent()

"""id_style
display_name
materials
color
size
price
currency
product_url
image_links
brand_name
retailer
description
scrapped_date
high_level
low_level
gender
secondhand
shipping_from
style"""

import json

def get_beauty_brands():
    """
        Gets all of the brands in the "face & body" section of Asos Women
    """
    URL = https://www.asos.com/us/women/
    response = requests.get(URL, headers={"User-Agent": user_agent})
    if response.status_code != http.client.OK:
        logging.error(f"Error retrieving {URL}: {response.status_code}")
        sys.exit()
    soup = BeautifulSoup(response.content.decode("utf-8"), "lxml")

def test_func():
    json_file = open('scraping-py\stop_words.json')
    stop_words = set(json.load(json_file)['stop_words'])
    #print(stop_words)

if __name__ == "__main__":
    test_func()
