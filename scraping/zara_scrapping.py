"""
This file scrapes the Zara website and all available products.

Author: Sarah Amiraslani
"""
# TODO: can add better exception handling

import re
import sys
import time
import csv
from pprint import pprint
from datetime import datetime
import random

import http.client
import logging

import requests
from bs4 import BeautifulSoup

import pandas as pd
import numpy as np

from utilities.helper_functions import get_user_agent

# set user agent to imitate browser requests
user_agent: str = get_user_agent()

def get_categories():
    """get links to each current category on zara us page"""

    start_time = time.time()

    # get zara us homepage content, store as bs4 object
    # use lxml as it's faster than html.parser
    URL = "https://www.zara.com/us/"
    response = requests.get(URL, headers={"User-Agent": user_agent})
    if response.status_code != http.client.OK:
        logging.error(f"Error retrieving {URL}: {response.status_code}")
        sys.exit()
    soup = BeautifulSoup(response.content.decode("utf-8"), "lxml")

    # get all the links to the clothing categories (e.g., HOME, WOMEN),
    # store in dict with name:href format

    # stopwords is a set to improve lookup speed
    stopwords = set(
        [
            "+ info",
            "about",
            "gift receipt",
            "gift card",
            "giftcard",
            "suppliers",
            "vr store",
            "press",
            "newsletter",
            "movie",
            "careers",
            "annual report",
            "company",
            "contact us",
            "help",
            "stores",
            "zaraseries",
            "stories",
            "zaratribute",
            "community support",
            "join life",
            "join life collection",
            "job",
            "join",
        ]
    )

    cat_links = {}

    # get links within a_tags
    for cat in soup.find_all("a", class_=re.compile(".+category.+")):

        # the text of the a tag will serve as the category name
        name: str = cat.get_text().strip().lower().replace("|", " ")

        # ignore specified categories
        if name in stopwords:
            continue

        # get link
        link = cat.get("href")

        # avoid a_tags with no link (None) and internal, same page links
        if not link or link.startswith("#"):
            continue

        # if we don't have the link and key is valid, add k,v pair to the dict
        if link not in cat_links.values():
            # format key
            key = " ".join(link.split("/")[-1].split("-")[0:-1])

            # if the key contains any of the stopwords or is empty,
            # ignore that link move to the next category
            if any(word in stopwords for word in key.split()) or key == "":
                continue

            cat_links[key] = link

    # some categories are within li_tags, get those as previous loop doesn't
    for li_tag in soup.find_all("li", class_=re.compile(".+category.+")):

        for cat in li_tag.select("a"):

            name: str = cat.get_text().strip().lower().replace("|", " ")

            # ignore specified categories
            if name in stopwords:
                continue

            # get link for category
            link = cat.get("href")

            # avoid a_tags with no link (None) and internal, same page links
            if not link or link.startswith("#"):
                continue

            # if we don't have the link and key is valid,
            # add k,v pair to the dict
            if link not in cat_links.values():
                # format key
                key = " ".join(link.split("/")[-1].split("-")[0:-1])

                # if the key contains any of the stopwords or is empty,
                # ignore that link
                if any(word in stopwords for word in key.split()) or key == "":
                    continue

                cat_links[key] = link

    print('get categories')
    print("--- %s seconds ---" % (time.time() - start_time),'\n')

    return cat_links


def get_items(cat_links):
    """get links to each item currently for sale on the zara us page"""

    item_links = {}
    start_time = time.time()

    # todo: [0:10] is for testing purposes, remove for production
    # make a html request with URL of each category
    for URL in list(cat_links.values())[0:10]:

        # make html request, save to bs4 obj
        response = requests.get(URL, headers={"User-Agent": user_agent})
        if response.status_code != http.client.OK:
            logging.error(f"Error retrieving {URL}: {response.status_code}")
            continue
        soup = BeautifulSoup(response.content.decode('utf-8'), "lxml")

        # get the link and name of each item in category
        for li_tag in soup.find_all("li", class_=re.compile(".+product.+")):

            for item in li_tag.select("a", class_=re.compile(".+item.+")):
                link = item.get("href")
                name = item.get_text().lower()

                # print('a_tag',a_tag)
                # print("link: ", link)
                # if the a_tag doesn't contain text, try the img tag
                if name == '':
                    try:
                        name = item.select("img")[0].get("alt").lower()
                    except:
                        name = ' '.join(link.split('/')[-1].split('-')[0:-1])

                # format name: remove unicode representing spaces
                name = name.replace(u'\xa0', u' ')

                # if we don't have the link, add k,v pair to the dict
                if link not in item_links.values() and name != '':

                    # it is possible for multiple items to share a name, which would overwite previous k:v pair
                    # if name it in dict, but link is different, rename the name
                    if name in item_links.keys():
                        name += str(random.randint(0,9))+str(random.randint(0,9))

                    item_links[name] = link

    print('get items')
    print("--- %s seconds ---" % (time.time() - start_time),'\n')

    return item_links


def get_item_data(item_links):
    """get material, colors, sizes, description, url, image, brand name, and retailer"""

    item_data = {}

    # ===== define arrays which will be used to construct DataFrame =====

    # initialize empty arrays for appending to
    high_array, low_array, dt_array,brand_array, retailer_array, secondhand_array, shipping_array, style_array, id_array, name_array, desc_array, color_array, sizes_array, pics_array, price_array, currency_array = ([], ) * 16

    for URL in list(item_links.values())[0:10]:
        print(URL)

        # make http request to get data for the item, save to bs4 obj
        response = requests.get(URL,headers={"User-Agent": user_agent})
        if response.status_code != http.client.OK:
            logging.error(f"Error retrieving {URL}: {response.status_code}")
            sys.exit()
        soup = BeautifulSoup(response.content.decode("utf-8"), "lxml")

        # colors
        # First, define a list of availble colors as we will need to itterate over the len(colors) and append each attribute (e.g., sizes, dec) len(colors) number of times
        colors = soup.find_all('p',class_=re.compile(".+color.+"))
        re_pattern = r"\|.[0-9]+\/[0-9]+"
        # format color, each element in color_array is a list
        if len(colors) == 1:
            colors = colors[0].text
            colors = list(
                re.sub(re_pattern,"",colors).replace('Color','').strip()
                )
        elif len(colors) > 1:
            colors = [
                re.sub(re_pattern,"",color.text).replace('Color', '').strip() for color in color
                ]
        n_colors = len(colors)

        # ===== product name =====
        # assumption: product is the only h1 tag
        name = soup.find_all('h1')
        if len(name) == 1:
            name:str = name[0].text.title()
        else:
            raise Exception("Invalid assumption, add conditions")
        name_array.extend(n_colors * [name])
        print('name: ',name)

        # =====  description =====
        # assumption: description comes before color
        # TODO: check that this is a valid assumption, add exception checking
        desc:str = soup.find_all('p')[0].text
        desc_array.extend(n_colors * [desc])
        print('description: ',desc)

        # ===== sizes =====
        # format size, each element in sizes_array is a list
        spans=soup.find_all('span',class_=re.compile('.+size-info__main-label'))
        sizes = [span.text.lower() for span in spans]
        sizes_array.extend(n_colors * [sizes])
        print('sizes: ',sizes)

        # ===== images =====
        # format image, each element in images_array is a list
        pics = soup.find_all("picture")
        pics_set =[
            str(i['srcset']).split()[0] for i in [pic.source for pic in pics]
            ]
        pics_array.extend(n_colors * [pics_set])
        print('pics set: ', pics_set)

        # ===== price and currency =====
        # assumption: first item in the carousel is the price
        price=soup.find_all('span',class_='price__amount-current')[0].text
        s = price.split()
        price,currency = s[0],s[-1]
        price_array.extend(n_colors * [price])
        currency_array.extend(n_colors * [currency])
        print('price',price)
        print('currency',currency)

        # ===== color and id style =====
        for color in colors:
            color_array.append(color)
            id_array.append('zara-' + name + '-' + color)

        # ==== material ====
        # material = soup.find('div',{'class':"structured-component-text-block-paragraph"})
        spans = soup.find_all('span')

        children = []
        for span in spans:
            children.extend(span.findChildren())
        grand_children = []
        for span in children:
            grand_children.extend(span.findChildren())

        # print('spans: ',spans)
        # <div class="structured-component-text-block-subtitle"><span class="structured-component-text zds-body-s"><span>BASE FABRIC</span></span></div>
        print('grand children: ',grand_children)
        # print('children: ',children)
        # soup.find_all('title', limit=1)
        # print('material: ',material)
        # print('Soup: testing for material: ',visible_text)
        # block = soup.find('div', attrs={'class': 'product-detail-view__main'})
        # # for span in badges.span.find_all('span', recursive=False):
        # #     print span.attrs['title']
        # print(block)

        # ==== gender ====
        #TODO: this is not working, look into https://www.geeksforgeeks.org/python-check-substring-present-given-string/
        text = soup.get_text(strip=True).split()

        for i,string in enumerate(text):
            if not string.find('woman'):
                text.pop(i)


        # high level

        # low level

        # https://www.zara.com/sitemaps/sitemap-us-en.xml.gz

        # print(text)

        # ==== fill arrays whose contents are known without parsing html ====
        dt_array.extend(n_colors*[str(datetime.today())])
        brand_array.extend(n_colors*['Zara'])
        retailer_array.extend(n_colors*['Zara'])
        secondhand_array.extend(n_colors*['No'])
        shipping_array.extend(n_colors*(np.nan))
        style_array.extend(n_colors*[np.nan])

        # create DataFrame (make sure to order array correctly)

        # rename columns in the DataFrame

    return item_data





def write_csvs():
    """add data to local csv and text files"""

    # TODO: I believe we have since added more fields, update csv structure

    with open("zara_table.csv", mode="w") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "Name",
                "Material",
                "Color",
                "Size",
                "Price",
                "URL",
                "Image",
                "Brand_name",
                "Description",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    with open("failed_zara.txt", mode="w") as txt_file:
        for row in failed:
            txt_file.write(str(row) + "\n")


def post_db():
    """post to postgress marketplace database"""
    pass


if __name__ == "__main__":

    cat_links = get_categories()
    item_links = get_items(cat_links)
    item_data = get_item_data(item_links)
