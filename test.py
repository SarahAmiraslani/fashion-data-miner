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

from helper_functions import get_user_agent

parent_index = "https://www2.hm.com/en_us.sitemap.xml"

# set user agent to imitate browser requests
user_agent: str = get_user_agent()
resp = requests.get(parent_index,{"User-Agent": user_agent})

print(user_agent)
print(resp)