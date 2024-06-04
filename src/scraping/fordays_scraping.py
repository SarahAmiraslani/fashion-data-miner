import requests
import csv
from bs4 import BeautifulSoup
from urllib.request import urlopen

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import chromedriver_binary  # Adds chromedriver binary to path
import json

import pandas as pd
import numpy as np
import httplib2
import re


def single_product(url, brand_name="Fordays"):

    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "lxml")
    name = soup.find("title").text.strip()
    res = soup.find_all("div", {"class": "column main"})

    for i in res:
        # description
        description_res = i.find_all("div", {"class": "short_description"})
        description = (
            [elem.text.strip() for elem in description_res]
            if len(description_res) > 0
            else None
        )

        # fabric
        fabric_res = i.find_all("span", {"itemprop": "fabric_detail"})
        fabric = (
            [elem.text.strip() for elem in fabric_res] if len(fabric_res) > 0 else None
        )

        # image
        img_list = i.find_all("img", {"class": "lozad"})
        img = [elem["data-src"] for elem in img_list] if len(img_list) > 0 else None
        if img:
            img = img[0]

        # price
        price_list = i.find_all("span", {"class": "price"})
        price = (
            [elem.text.strip() for elem in price_list] if len(price_list) > 0 else None
        )

    # high level
    hl = 0
    if (
        (re.search(r"\s?shirts?\b", name.lower()) is not None)
        and (re.search(r"\s?t-shirts\b", name.lower()) is None)
        or (re.search(r"\s?tops?\b", name.lower()) is not None)
        or (re.search(r"\s?cami?\b", name.lower())is not None)
        or (re.search(r"\s?polo?\b", name.lower()) is not None)
        or (re.search(r"\s?tank?\b", name.lower()) is not None)
        or (re.search(r"\s?blouse?\b", name.lower()) is not None)
        or (re.search(r"\s?crop?\b", name.lower()) is not None)
        or (re.search(r"\s?tee?\b", name.lower()) is not None)
        or (re.search(r"\s?sleeves?\b", name.lower()) is not None)
    ):
        hl = 1
    elif (
        (re.search(r"\s?hoody?i?e?s?\b", name.lower()) is not None)
        or (re.search(r"\s?jumpers?\b", name.lower()) is not None)
        or (re.search(r"\s?sweaters?\b", name.lower()) is not None)
        or (re.search(r"\s?blazers?\b", name.lower()) is not None)
        or (re.search(r"\s?fleece?\b", name.lower()) is not None)
        or (re.search(r"\s?cardi?\b", name.lower()) is not None)
    ):
        hl = 2
    elif (
        (re.search(r"\s?shorts?\b", name.lower()) is not None)
        or (re.search(r"\s?sk[io]rts?\b", name.lower()) is not None)
        or (re.search(r"\s?trouser?s?\b", name.lower()) is not None)
        or (re.search(r"\s?pants?\b", name.lower()) is not None)
        or (re.search(r"\s?[jl]eggings?\b", name.lower()) is not None)
        or (re.search(r"\s?joggers?\b", name.lower()) is not None)
        or (re.search(r"\s?jeans?\b", name.lower()) is not None)
        or (re.search(r"\s?bottoms?\b", name.lower()) is not None)
        or (re.search(r"\s?sweats?\b", name.lower()) is not None)
        or (re.search(r"\s?culottes?\b", name.lower()) is not None)
    ):
        hl = 3
    elif (
        (re.search(r"\s?dress?\b", name.lower()) is not None)
        or (re.search(r"\s?romper?\b", name.lower()) is not None)
        or (re.search(r"\s?jumpsuit?\b", name.lower()) is not None)
        or (re.search(r"\s?chemise?\b", name.lower()) is not None)
        or (re.search(r"\s?overalls?\b", name.lower()) is not None)
        or (re.search(r"\s?salopettes?\b", name.lower()) is not None)
    ):
        hl = 4
    elif (
        (re.search(r"\s?jackets?\b", name.lower()) is not None)
        or (re.search(r"\s?shackets?\b", name.lower()) is not None)
        or (re.search(r"\s?parka?\b", name.lower()) is not None)
        or (re.search(r"\s?cardigan?\b", name.lower()) is not None)
        or (re.search(r"\s?gilets?\b", name.lower()) is not None)
        or (re.search(r"\s?coat?\b", name.lower()) is not None)
        or (re.search(r"\s?vest?\b", name.lower()) is not None)
        or (re.search(r"\s?trench?\b", name.lower()) is not None)
    ):
        hl = 5
    elif (
        (re.search(r"\s?bra?\b", name.lower()) is not None)
        or (re.search(r"\s?bodysuit?\b", name.lower()) is not None)
        or (re.search(r"\s?body?\b", name.lower()) is not None)
        or (re.search(r"\s?robe?\b", name.lower()) is not None)
        or (re.search(r"\s?briefs?\b", name.lower()) is not None)
        or (re.search(r"\s?underwear?\b", name.lower()) is not None)
        or (re.search(r"\s?thong?\b", name.lower()) is not None)
        or (re.search(r"\s?camisoles?\b", name.lower()) is not None)
        or (re.search(r"\s?tights\b", name.lower()) is not None)
    ):
        hl = 6
    elif (
        (re.search(r"\s?bikini?\b", name.lower()) is not None)
        or (re.search(r"\s?swimsuit?\b", name.lower()) is not None)
        or (re.search(r"\s?trunks?\b", name.lower()) is not None)
    ):
        hl = 7
    elif (
        (re.search(r"\s?caps?\b", name.lower()) is not None)
        or (re.search(r"\s?hats?\b", name.lower()) is not None)
        or (re.search(r"\s?fedora?\b", name.lower()) is not None)
        or (re.search(r"\s?beanies?\b", name.lower()) is not None)
        or (re.search(r"\s?beret?\b", name.lower()) is not None)
    ):
        hl = 8
    elif (
        (re.search(r"\s?bags?\b", name.lower()) is not None)
        or (re.search(r"\s?backpack?\b", name.lower()) is not None)
        or (re.search(r"\s?purse?\b", name.lower()) is not None)
        or (re.search(r"\s?fanny?\b", name.lower()) is not None)
    ):
        hl = 9
    elif (
        (re.search(r"\s?shoes?\b", name.lower()) is not None)
        or (re.search(r"\s?trainers?\b", name.lower()) is not None)
        or (re.search(r"\s?loafers?\b", name.lower()) is not None)
        or (re.search(r"\s?boots?\b", name.lower()) is not None)
        or (re.search(r"\s?sandals?\b", name.lower()) is not None)
        or (re.search(r"\s?mules?\b", name.lower()) is not None)
        or (re.search(r"\s?sneakers?\b", name.lower()) is not None)
        or (re.search(r"\s?wellies?\b", name.lower()) is not None)
        or (re.search(r"\s?flats?\b", name.lower()) is not None)
        or (re.search(r"\s?slider?s?\b", name.lower()) is not None)
        or (re.search(r"\s?flops?\b", name.lower()) is not None)
        or (re.search(r"\s?pumps?\b", name.lower()) is not None)
        or (re.search(r"\s?espadrilles?\b", name.lower()) is not None)
        or (re.search(r"\s?heels?\b", name.lower()) is not None)
        or (re.search(r"\s?plimsolls?\b", name.lower()) is not None)
    ):
        hl = 10
    elif (
        (re.search(r"\s?belts?\b", name.lower()) is not None)
        or (re.search(r"\s?gloves?\b", name.lower()) is not None)
        or (re.search(r"\s?scarf\b", name.lower()) is not None)
        or (re.search(r"\s?rings?\b", name.lower()) is not None)
        or (re.search(r"\s?bracelets?\b", name.lower()) is not None)
        or (re.search(r"\s?necklaces?\b", name.lower()) is not None)
        or (re.search(r"\s?glasses\b", name.lower()) is not None)
        or (re.search(r"\s?braces?\b", name.lower()) is not None)
        or (re.search(r"\s?earringa?s?\b", name.lower()) is not None)
        or (re.search(r"\s?headbands?\b", name.lower()) is not None)
        or (re.search(r"\s?wallet\b", name.lower()) is not None)
        or (re.search(r"\s?suspenders?\b", name.lower()) is not None)
        or (re.search(r"\s?clutch\b", name.lower()) is not None)
        or (re.search(r"\s?pendants?\b", name.lower()) is not None)
        or (re.search(r"\s?socks?\b", name.lower()) is not None)
        or (re.search(r"\s?mittens?\b", name.lower()) is not None)
    ):
        hl = 11

    # category
    cat = 0
    if (
        (re.search(r"\s?shirts?\b", name.lower()) is not None)
        and (re.search(r"\s?t-shirts\b", name.lower()) is None)
        or (re.search(r"\s?tops?\b", name.lower()) is not None)
        or (re.search(r"\s?cami?\b", name.lower()) is not None)
        or (re.search(r"\s?polo?\b", name.lower()) is not None)
        or (re.search(r"\s?tank?\b", name.lower()) is not None)
        or (re.search(r"\s?blouse?\b", name.lower()) is not None)
        or (re.search(r"\s?crop?\b", name.lower()) is not None)
        or (re.search(r"\s?tee?\b", name.lower()) is not None)
    ):
        cat = 1
    elif (
        (re.search(r"\s?jumpers?\b", name.lower()) is not None)
        or (re.search(r"\s?blazers?\b", name.lower()) is not None)
        or (re.search(r"\s?sweaters?\b", name.lower()) is not None)
        or (re.search(r"\s?sleeves?\b", name.lower()) is not None)
        or (re.search(r"\s?fleece?\b", name.lower()) is not None)
        or (re.search(r"\s?cardi\b", name.lower()) is not None)
    ):
        cat = 2
    elif re.search(r"\s?hoody?i?e?s?\b", name.lower()) is not None:
        cat = 3
    elif re.search(r"\s?shorts?\b", name.lower()) is not None:
        cat = 4
    elif re.search(r"\s?sk[io]rts?\b", name.lower()) is not None:
        cat = 5
    elif (
        (re.search(r"\s?trouser?s?\b", name.lower()) is not None)
        or (re.search(r"\s?pants?\b", name.lower()) is not None)
        or (re.search(r"\s?culottes?\b", name.lower()) is not None)
    ):
        cat = 6
    elif (
        (re.search(r"\s?[jl]eggings?\b", name.lower()) is not None)
        or (re.search(r"\s?joggers?\b", name.lower()) is not None)
        or (re.search(r"\s?bottoms?\b", name.lower()) is not None)
        or (re.search(r"\s?sweats?\b", name.lower()) is not None)
    ):
        cat = 7
    elif re.search(r"\s?jeans?\b", name.lower()) is not None:
        cat = 8
    elif (re.search(r"\s?dress?\b", name.lower()) is not None) or (
        re.search(r"\s?chemise?\b", name.lower()) is not None
    ):
        cat = 9
    elif (
        (re.search(r"\s?romper?\b", name.lower()) is not None)
        or (re.search(r"\s?overalls?\b", name.lower()) is not None)
        or (re.search(r"\s?jumpsuit?\b", name.lower()) is not None)
        or (re.search(r"\s?salopettes?\b", name.lower()) is not None)
    ):
        cat = 10
    elif (
        (re.search(r"\s?jackets?\b", name.lower()) is not None)
        or (re.search(r"\s?shackets?\b", name.lower()) is not None)
        or (re.search(r"\s?parka?\b", name.lower()) is not None)
        or (re.search(r"\s?cardigan?\b", name.lower()) is not None)
        or (re.search(r"\s?gilets?\b", name.lower()) is not None)
        or (re.search(r"\s?coat?\b", name.lower()) is not None)
        or (re.search(r"\s?vest?\b", name.lower()) is not None)
        or (re.search(r"\s?trench?\b", name.lower()) is not None)
    ):
        cat = 11
    elif (
        (re.search(r"\s?bra?\b", name.lower()) is not None)
        or (re.search(r"\s?bodysuit?\b", name.lower()) is not None)
        or (re.search(r"\s?body?\b", name.lower()) is not None)
        or (re.search(r"\s?robe?\b", name.lower()) is not None)
        or (re.search(r"\s?briefs?\b", name.lower()) is not None)
        or (re.search(r"\s?underwear?\b", name.lower()) is not None)
        or (re.search(r"\s?thong?\b", name.lower()) is not None)
        or (re.search(r"\s?camisoles?\b", name.lower()) is not None)
        or (re.search(r"\s?tights\b", name.lower()) is not None)
    ):
        cat = 12
    elif (
        (re.search(r"\s?bikini?\b", name.lower()) is not None)
        or (re.search(r"\s?swimsuit?\b", name.lower()) is not None)
        or (re.search(r"\s?trunks?\b", name.lower()) is not None)
    ):
        cat = 13
    elif (
        (re.search(r"\s?caps?\b", name.lower()) is not None)
        or (re.search(r"\s?hats?\b", name.lower()) is not None)
        or (re.search(r"\s?fedora?\b", name.lower()) is not None)
        or (re.search(r"\s?beanies?\b", name.lower()) is not None)
        or (re.search(r"\s?beret?\b", name.lower()) is not None)
    ):
        cat = 14
    elif (
        (re.search(r"\s?bags?\b", name.lower()) is not None)
        or (re.search(r"\s?backpack?\b", name.lower()) is not None)
        or (re.search(r"\s?purse?\b", name.lower()) is not None)
        or (re.search(r"\s?fanny?\b", name.lower()) is not None)
    ):
        cat = 15
    elif (
        (re.search(r"\s?shoes?\b", name.lower()) is not None)
        or (re.search(r"\s?trainers?\b", name.lower()) is not None)
        or (re.search(r"\s?loafers?\b", name.lower()) is not None)
        or (re.search(r"\s?boots?\b", name.lower()) is not None)
        or (re.search(r"\s?sandals?\b", name.lower()) is not None)
        or (re.search(r"\s?mules?\b", name.lower()) is not None)
        or (re.search(r"\s?sneakers?\b", name.lower()) is not None)
        or (re.search(r"\s?wellies?\b", name.lower()) is not None)
        or (re.search(r"\s?flats?\b", name.lower()) is not None)
        or (re.search(r"\s?slider?s?\b", name.lower()) is not None)
        or (re.search(r"\s?flops?\b", name.lower()) is not None)
        or (re.search(r"\s?pumps?\b", name.lower()) is not None)
        or (re.search(r"\s?espadrilles?\b", name.lower()) is not None)
        or (re.search(r"\s?heels?\b", name.lower()) is not None)
        or (re.search(r"\s?plimsolls?\b", name.lower()) is not None)
    ):
        cat = 16
    elif (
        (re.search(r"\s?belts?\b", name.lower()) is not None)
        or (re.search(r"\s?gloves?\b", name.lower()) is not None)
        or (re.search(r"\s?scarf\b", name.lower()) is not None)
        or (re.search(r"\s?rings?\b", name.lower()) is not None)
        or (re.search(r"\s?bracelets?\b", name.lower()) is not None)
        or (re.search(r"\s?necklaces?\b", name.lower()) is not None)
        or (re.search(r"\s?glasses\b", name.lower()) is not None)
        or (re.search(r"\s?braces?\b", name.lower()) is not None)
        or (re.search(r"\s?earringa?s?\b", name.lower()) is not None)
        or (re.search(r"\s?headbands?\b", name.lower()) is not None)
        or (re.search(r"\s?wallet\b", name.lower()) is not None)
        or (re.search(r"\s?suspenders?\b", name.lower()) is not None)
        or (re.search(r"\s?clutch?\b", name.lower()) is not None)
        or (re.search(r"\s?pendant\b", name.lower()) is not None)
        or (re.search(r"\s?socks?\b", name.lower()) is not None)
        or (re.search(r"\s?mittens?\b", name.lower()) is not None)
        or (re.search(r"\s?ear\b", name.lower()) is not None)
    ):
        cat = 17
    if price:
        price = price[0]
    return {
        "Name": name,
        "Material": fabric,
        "Color": None,
        "Price": price,
        "URL": url,
        "Image": img,
        "Brand_name": brand_name,
        "Description": description,
        "high-level": hl,
        "category": cat,
    }


def get_all_item_links(url):
    response = requests.get(url)
    results_page = BeautifulSoup(response.content.decode("utf-8"), "lxml")
    view_all_links = [url]
    # print("results_page =", results_page) debugging
    page = results_page.find("ul", {"class": "pagination"})
    # print("page =", page) debugging
    page_list = page.find_all("a", {"class": "page"})
    # print("page_list =", page_list) debugging
    for p in page_list:
        page_link = p.get("href")
        if page_link == "#":
            continue
        view_all_links.append(page_link)

    url_list = []
    for url in view_all_links:
        response = requests.get(url)
        results_page = BeautifulSoup(response.content.decode("utf-8"), "lxml")
        items = results_page.find_all("a", {"class": "product-item-link"})
        for item in items:
            url_list.append(item.get("href"))

    return url_list


fordays = []
url_list = get_all_item_links("https://www.fordays.com/all/women")
for url in url_list:
    fordays.append(single_product(url))
url_list = get_all_item_links("https://www.fordays.com/all/men")
for url in url_list:
    fordays.append(single_product(url))

len(fordays)
with open("fordays_table.csv", "w", encoding="utf-8") as f:
    # Using dictionary keys as fieldnames for the CSV file header
    writer = csv.DictWriter(f, fordays[0].keys())
    writer.writeheader()
    for d in fordays:
        writer.writerow(d)
