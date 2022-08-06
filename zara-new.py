import os
import json
import csv
import re

from pathlib import Path
from itertools import repeat
from datetime import datetime

import numpy as np

from bs4 import BeautifulSoup
import requests
import http.client
import logging

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from helper_functions import (
    get_high_level,
    get_low_level,
    get_user_agent,
    prep_driver,
    part_matching,
    materials_matching,
)

url = "https://www.zara.com/sitemaps/sitemap-us-en.xml"

# set user agent to imitate browser requests
user_agent: str = get_user_agent()


def parse_sitemap(url: str):
    '''get all product urls from the sitemap'''
    resp = requests.get(url, headers={"User-Agent": user_agent})
    # we didn't get a valid response, bail
    if 200 != resp.status_code:
        return False

    # BeautifulSoup to parse the document
    soup = BeautifulSoup(resp.content, "xml")

    # find all the product urls in the html
    urls = [u.find("loc").string for u in soup.findAll("url")]
    regex = re.compile(r"p\d+\.html")
    prod_urls = [u for u in urls if regex.search(u)]

    return prod_urls


def get_item_data(prod_urls: list):
    '''for each product url get all attributes of interest'''

    for url in prod_urls:

        # make http request to get data for the item, save to bs4 obj
        response = requests.get(url, headers={"User-Agent": user_agent})

        # continue to the next url if not a valid response
        if response.status_code != http.client.OK:
            logging.error(f"Error retrieving {url}: {response.status_code}")
            continue
        soup = BeautifulSoup(response.content.decode("utf-8"), "lxml")

        # ==== colors ====
        colors = soup.find_all("p", class_=re.compile(".+color.+"))
        re_pattern = r"\|.[0-9]+\/[0-9]+"
        if len(colors) == 1:
            colors = [
                re.sub(re_pattern, "", colors[0].text).replace("Color", "").strip()
            ]
        elif len(colors) > 1:
            colors = [
                re.sub(re_pattern, "", color.text).replace("Color", "").strip()
                for color in colors
            ]
        # Note: we will append each attribute len(colors) number of times
        n_colors = len(colors)
        color = [color for color in colors]
        print("color: ", color)

        # ===== product name and url =====
        # assumption: product is the only h1 tag
        name = soup.find_all("h1")
        if len(name) == 1:
            name: str = name[0].text.title()
        else:
            raise Exception("Invalid assumption, add conditions")

        display_name = list(repeat(name, n_colors))
        product_url = list(repeat(url, n_colors))
        print("name: ", display_name)
        print("url: ", product_url)

        # ==== id style ====
        id_style = [
            "zara-" + "-".join(name.split()) + "-" + "-".join(color.split())
            for color in colors
        ]
        print("id: ", id_style)

        # ==== id clothing ====
        id = str(datetime.today().date()).replace("-", "") + "zara" + str(name).replace(" ","")
        clothing_id = list(repeat(id, n_colors))

        # =====  description =====
        # assumption: description comes before color
        # TODO: check that this is a valid assumption, add exception checking
        description = list(repeat(soup.find_all("p")[0].text, n_colors))
        print("description: ", description)

        # ===== sizes =====
        # format size, each element in sizes_array is a list
        spans = soup.find_all("span", class_=re.compile(".+size-info__main-label"))
        size = list(repeat([span.text.lower() for span in spans], n_colors))
        print("sizes: ", size)
        # TODO: sometimes scrapper doesn't get the needed size data: e.g., I ran the script right after one another and once it returned the sizes and the other times it didn't.

        # ===== images =====
        # format image, each element in images_array is a list
        pics = soup.find_all("picture")
        pics_set = [str(i["srcset"]).split()[0] for i in [pic.source for pic in pics]]
        image_links = list(repeat(pics_set, n_colors))
        print("image links: ", image_links)

        # ===== price and currency =====
        # assumption: first item in the carousel is the price
        price = soup.find_all("span", class_="price__amount-current")[0].text
        s = price.split()
        price, currency = list(repeat(s[0], n_colors)), list(repeat(s[-1], n_colors))
        print("price_array: ", price)
        print("currency_array: ", currency)

        # ==== gender ====
        text = soup.get_text().split("/")
        copyright_i = [i for i, t in enumerate(text) if "©" in t][0]
        gender = list(repeat(text[copyright_i - 1].strip().lower(), n_colors))
        print("gender: ", gender)

        # ==== scraped date ====
        scrapped_date = list(repeat(str(datetime.today().date()), n_colors))
        print("scrapped date: ", scrapped_date)

        # ==== secondhand ===
        secondhand = list(repeat("0", n_colors))
        print("secondhand: ", secondhand)

        # ==== brand and retailer ===
        brand_name = list(repeat("Zara", n_colors))
        retailer = list(repeat("Zara", n_colors))
        print("brand name: ", brand_name)
        print("retailer: ", retailer)

        # ==== style ====
        style = list(repeat(np.nan, n_colors))
        print("style: ", style)

        # ==== shipping ====
        shipping_from = list(repeat(np.nan, n_colors))
        print("shipping from", shipping_from)

        # ==== availability ====
        availability = list(repeat(1, n_colors))
        print("availability: ", availability)

        # ==== high and low level ====
        ll = get_low_level(name, description)
        low_level = list(repeat(ll, n_colors))
        print("low_level: ", low_level)

        hl = get_high_level(ll)
        high_level = list(repeat(hl, n_colors))
        print("high_level: ", high_level)

        # ==== materials ====

        # because materials data is within a JavaScript embedding, requests.get() doesn't parse these. Selenium, on the other hand, does.

        # instantiate webdriver and navigate to the page
        # pretend to be a different user upon each new request
        options = prep_driver(user_agent=get_user_agent())
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        driver.get(url)

        # driver.maximize_window()

        # get page content and parse to the materials details
        materials = {}
        materials_soup = BeautifulSoup(driver.page_source, "lxml")
        details = materials_soup.find_all("span", class_="structured-component-text")
        details_txt = [i.text for i in details]

        # find all indices that have % sign, get the content of those indices
        p_indices = [i for i, s in enumerate(details_txt) if "%" in s]
        c_indices = [i - 1 for i, s in enumerate(details_txt) if "%" in s]

        # create a list of parts and materials
        p_text = [i.split() for i in [details_txt[i] for i in p_indices]]
        for i, c_i in enumerate(c_indices):
            p_text[i].insert(0, details_txt[c_i])

        # e.g., p_text is [['BASE FABRIC', '100%', 'cotton'], ['COATING', '100%', 'polyurethane', 'thermoplastic'], ['LINING', '80%', 'wool', '·', '20%', 'nylon']]

        for l in p_text:
            # remove unwanted chars from list
            if "·" in l:
                l.remove("·")
            # if item is made of only one material
            # e.g., ['BASE FABRIC', '100%', 'cotton']
            if len(l) == 3:
                # e.g., materials = {'BASE FABRIC': {'cotton':'100%'}}
                materials[l[0]] = {l[-1]: l[1]}
            # if item is made of multiple materials
            # e.g., ['LINING', '80%', 'wool', '20%', 'nylon']
            if len(l) > 3:
                # get indices where % is present
                p_indices = [i for i, s in enumerate(l) if "%" in s]
                # if only 1 index, false alarm:
                # one material, material name has more than one word
                # e.g., ['COATING', '100%', 'polyurethane', 'thermoplastic']
                if len(p_indices) == 1:
                    # append to dict
                    # e.g.,materials = {'COATING': {'polyurethane', 'thermoplastic': '100%'}}
                    materials[l[0]] = {" ".join(l[2:]): l[1]}
                # there are actually multiple materials
                else:
                    # e.g., ['LINING', '80%', 'wool', '20%', 'nylon']
                    for loc, i in enumerate(p_indices):
                        if loc < len(p_indices) - 1:
                            next_perc = p_indices[loc + 1]
                        else:
                            next_perc = False

                        # if the first %, define the dict
                        if i == p_indices[0]:
                            materials[l[0]] = {" ".join(l[i + 1 : next_perc]): l[i]}
                        # else, append k:v pairs to the dict
                        else:
                            if next_perc == False:
                                materials[l[0]].update({" ".join(l[i + 1 :]): l[i]})
                            else:
                                materials[l[0]].update(
                                    {" ".join(l[i + 1 : next_perc]): l[i]}
                                )

        materials = list(repeat(materials, n_colors))
        print("materials: ", materials)

        parent_dir = parent_dir = str(Path(os.getcwd()).parent)

        # ---- CLOTHES TABLE ----
        clothes_dir = parent_dir + os.sep + "data" + os.sep + "clothes-tables"
        with open(clothes_dir + os.sep + "zara_table.csv", "a") as f:
            item_writer = csv.writer(
                f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
            )

            for i in range(n_colors):
                item_writer.writerow(
                    [
                        clothing_id[i],
                        id_style[i],
                        display_name[i],
                        materials[i],
                        color[i],
                        size[i],
                        price[i],
                        currency[i],
                        product_url[i],
                        image_links[i],
                        brand_name[i],
                        retailer[i],
                        description[i],
                        scrapped_date[i],
                        high_level[i],
                        low_level[i],
                        gender[i],
                        secondhand[i],
                        shipping_from[i],
                        style[i],
                        availability[i],
                    ]
                )

        # ---- ITEM_HAS_MATERIAL TABLE ----

        # Note: while materials and clothing_id will be of length n_colors, we will ignore this fact for the item_has_material table as all colors have the same materials (i.e., there is no use in writing the same info n_colors times)

        # itterate through the parts in the materials dictionary, append
        parts_dict = json.loads(str(materials[0]).replace("'", '"'))
        id = clothing_id[0]
        parts, materials, percs = [], [], []

        for part in parts_dict:

            materials_dict = parts_dict[part]

            for mat in materials_dict:
                parts.append(part_matching(part))
                materials.append(materials_matching(mat))
                percs.append(materials_dict[mat])

        item_mat_dir = parent_dir + os.sep + "data" + os.sep + "item-has-material-tables"
        with open(item_mat_dir+ os.sep + "zara_item_material.csv", "a") as f:
            mat_writer = csv.writer(
                f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
            )

            for i in range(len(materials)):
                mat_writer.writerow([
                    id,
                    materials[i],
                    parts[i],
                    percs[i]
                ])


if __name__ == "__main__":

    # get all products and their data, write to local csv file
    prod_urls = parse_sitemap(url)
    get_item_data(prod_urls)
