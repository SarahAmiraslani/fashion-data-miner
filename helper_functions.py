"""
This file contains general purpose functions that will be used to scrape various websites and process the resulting tables.
"""

from selenium import webdriver
import random
import extruct
import requests
from w3lib.html import get_base_url
import pandas as pd
import re
import os
from ast import literal_eval
import pprint
from extruct.microformat import MicroformatExtractor
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import numpy as np
from pathlib import Path
from datetime import datetime
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem


# ---- web scrapping ----


def get_metadata(url: str, type: str = "all-in-one") -> dict:
    """extract embedded metadata from HTML markup"""

    user_agent = get_user_agent()

    r = requests.get(url, headers={"User-Agent": user_agent})
    if type == "all-in-one":
        base_url = get_base_url(r.text, r.url)
        data = extruct.extract(r.text, base_url=base_url)
    elif type == "micro":
        microformat = MicroformatExtractor()
        data = microformat.extract(r.text)

    pprint.pprint(data, indent=4)

    return data


def get_sitemap(url: str,user_agent: str) -> str:

    req = Request(url, headers={"User-Agent": user_agent})
    response = urlopen(req).read().decode("utf-8")

    return response


def get_user_agent()->str:
    software_names = [SoftwareName.CHROME.value]
    operating_systems = [OperatingSystem.WINDOWS.value,OperatingSystem.MAC.value,OperatingSystem.LINUX.value]

    user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems,limit=100)

    user_agent = user_agent_rotator.get_random_user_agent()

    return user_agent


def prep_driver(user_agent: str):
    "prepare webdriver options, returns object of class 'selenium.webdriver.chrome.options.Options'"

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument('--no-sandbox')
    options.add_argument("--incognito")
    options.add_argument("--start-maximized")
    options.add_argument("--enable-automation")
    # options.add_argument("--window-size=1420,1080")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-gpu")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable')
    options.add_argument(f"user-agent={user_agent}")

    return options


# ---- standardizing data (CLOTHES db) ----


def get_low_level(name: str, desc:str ) -> str:

    parent_dir = str(Path(os.getcwd()).parent)
    ll_df = pd.read_csv(
        parent_dir
        + os.sep
        + "standardization-csvs"
        + os.sep
        + "LowLevelCatagoryRegex.csv",
        header=None,
        skiprows=[0],
    )

    # get all the low level categories regex patterns
    cats:list[str] = []
    for _, row in ll_df.iloc[:, 1:].iterrows():
        for i in ll_df.columns[1:]:
            if pd.isnull(row[i]):
                continue
            else:
                cats.append(row[i])

    # find the low level category regex that matches the input name (should match only one), get the corresponding low level category name
    for cat in cats:
        ll = "Other"
        if re.search(cat, name.lower()):
            ll = ll_df[(ll_df == cat).any(axis=1)].iloc[0, 0]
            break

        # if no re matches, try to use the description as a final try
        if ll == "Other":
            desc_words = [word.lower() for word in desc[0].split()]

            for word in desc_words:
                if re.search(cat, word):
                    ll = ll_df[(ll_df == cat).any(axis=1)].iloc[0, 0]

        # if ll is still other we need to update LowLevelCategoryRegex file
    return ll


def get_high_level(lower_level: str) -> str:
    parent_dir = str(Path(os.getcwd()).parent)
    hl_df = pd.read_csv(
        parent_dir
        + os.sep
        + "standardization-csvs"
        + os.sep
        + "HighLevelCatagory-LowLevelCatagory.csv"
    )

    # search for rows with that low level category (should match only one), get the corresponding high level category
    hl = hl_df[(hl_df == lower_level.title()).any(axis=1)].iloc[0, 0]

    return hl


# ---- standardizing data (item_has_material db) ----


def part_matching(raw_part:str) -> str:
    parent_dir = str(Path(os.getcwd()).parent)
    parts_df = pd.read_csv(
        parent_dir + os.sep + "standardization-csvs" + os.sep + "PartsRegex.csv"
    )

    # get all the parts regex patterns
    parts:list[str] = []
    for _, row in parts_df.iloc[:, 1:].iterrows():
        for i in parts_df.columns[1:]:
            if pd.isnull(row[i]):
                continue
            else:
                parts.append(row[i])

    for part in parts:
        p = 'All'
        if re.search(part, raw_part.strip().lower()):
            p = parts_df[(parts_df == part).any(axis=1)].iloc[0, 0]
            break

    return p


def materials_matching(raw_material: str):
    parent_dir = str(Path(os.getcwd()).parent)
    m_df = pd.read_csv(
        parent_dir + os.sep + "standardization-csvs" + os.sep + "MaterialProxy.csv"
    )

    # get all the materials regex patterns
    materials:list[str] = []
    for _, row in m_df.iloc[:, 1:].iterrows():
        for i in m_df.columns[1:]:
            if pd.isnull(row[i]):
                continue
            else:
                materials.append(row[i])

    for material in materials:
        m = 'other'
        if re.search(material, raw_material.strip().lower()):
            m = m_df[(m_df == material).any(axis=1)].iloc[0, 0]
            break

    return m


# ---- cleaning local files ----


def standardize_csvs(path):
    """
    note: path can be absolute or relative.

    According to ReadMe, final table needs to have:
    - display_name(str): title case
    - product_material(dict): material(str title case): material(str %)
    - color (str): title case
    - price (str): currency price
    - product_url: to that specific color if possible
    """
    df = pd.read_csv(path).rename(str.lower, axis="columns")
    cols = set(df.columns)

    # name column
    if "display_name" not in cols:

        # rename column
        if "name" in cols:
            df.rename(columns={"name": "display_name"}, inplace=True)

        # change the casing and strip of whitespace
        df.display_name = df.display_name.apply(lambda x: str(x).title().strip())

    # material column
    if "product_material" not in cols:

        # rename column
        if "material" in cols:
            df.rename(columns={"material": "product_material"}, inplace=True)

        df.material = df.material.apply(literal_eval)

        if isinstance(df.material[0], set):
            df.material = df.material.apply(lambda x: x.remove(""))

    # price column

    # url column

    # image column

# materials_matching("cotton")
# low_level('pajamas')
# high_level("Pajamas")

# part("Hood")

# ---- general helper functions ----

def saveList(np_array, filename):
    '''
    Saves numpy array to file

	Parameters:
	np_array (numpy array): numpy array
    filename (str): name of file to save to ('.npy')

    '''
    # the filename should mention the extension 'npy'
    np.save(filename,np_array)
    print("Saved successfully!")


def loadList(filename):
    '''
    Loads .npy file as numpy array

	Parameters:
    filename (str): name of file ('.npy')

    Returns:
    tempNumpyArray (numpy array)

    '''
    # the filename should mention the extension 'npy'
    tempNumpyArray=np.load(filename)
    return tempNumpyArray.tolist()
