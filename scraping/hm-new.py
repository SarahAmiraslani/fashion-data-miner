from bs4 import BeautifulSoup
import requests
import re
import http.client
import logging
import sys
from itertools import repeat
from datetime import datetime
import numpy as np
import pandas as pd
import os
from pathlib import Path

from utilities.helper_functions import get_user_agent

parent_index = "https://www2.hm.com/en_us.sitemap.xml"

# set user agent to imitate browser requests
user_agent: str = get_user_agent()


def parse_sitemap(url: str):
    resp = requests.get(url, headers={"User-Agent": user_agent})
    # we didn't get a valid response, bail
    if 200 != resp.status_code:
        return False

    # BeautifulSoup to parse the document
    soup = BeautifulSoup(resp.content, "xml")
    # print(soup)

    # find all the product urls in the html
    sitemaps = [i.string for i in soup.find_all("loc")]
    # print(sitemaps)

    responses = [
        BeautifulSoup(
            requests.get(map, headers={"User-Agent": user_agent}).content, "xml"
        )
        for map in sitemaps
    ]
    print(responses[0].find_all("href"))

    # urls = [soup.find("loc").string for soup in response]
    # regex = re.compile(r"p\d+\.html")
    # prod_urls = [u for u in urls if regex.search(u)]
    # print(loc)
    return prod_urls


if __name__ == "__main__":
    prod_urls = parse_sitemap(parent_index)
    print(prod_urls)
