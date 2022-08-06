"""
This file scrapes the hm website and all available products. Uses a webdriver and the requests module

Author: Sarah Amiraslani
"""

import re
import sys
import time
import csv
from pprint import pprint
from datetime import datetime
import random
import requests

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

import http.client
import logging

from helper_functions import get_user_agent, prep_driver

# set user agent to imitate browser requests
user_agent: str = get_user_agent()


def get_categories():
	"""get links to each current category on zara us page"""

	start_time = time.time()

	# get hm us homepage content, store as bs4 object
	# use lxml as it's faster than html.parser
	URL = "https://www2.hm.com/en_us/index.html"
	response = requests.get(URL, headers={"User-Agent": user_agent})
	if response.status_code != http.client.OK:
		logging.error(f"Error retrieving {URL}: {response.status_code}")
		sys.exit()
	soup = BeautifulSoup(response.content.decode("utf-8"), "lxml")

	# stopwords is a set to improve lookup speed
	stopwords = set(
		[
			"HM.com",
			"My Account",
			"Not a Member yet? Join here!",
			"Sign out",
			"Favorites",
			"Shopping bag(0)",
			"Sign in",
			"Skip navigation",
			"Loyalty Program Info",
			"Student Discount: Get 15% off",
			"Gift Cards",
			"H&M Take Care",
			"Learn More",
			"Higg Index",
			"Magazine",
			"Dog clothes & Accessories",
			"Care products",
			"Dinnerware & Tableware",
			"Home Storage & Organizing",
			"Bedding",
			"Throw Pillows & Seat Cushions",
			"Decorations",
			"Rugs",
			"Bath & Shower",
			"Blankets",
			"Curtains",
			"Toys",
			"Cookware & Bakeware",
			"Gift wrapping",
			"H&M HOME",
			"Beauty",
			"Living room",
			"Kitchen",
			"Bedroom",
			"Bathroom",
			"Kids' Room",
			"Outdoor",
			"Decorations",
			"Storage",
			"Bed Linen",
			"Pillows",
			"The latest",
			"Let's change",
			"Let's innovate",
			"Let's be fair",
			"Sustainability",
			"Let's be for all",
			"Let's be transparent",
			"Let's clean up",
			"Let's close the loop",
			"Praise from others",
			"Conscious products explained",
			"Repair, remake & refresh",
			"H&M Group Sustainability Strategy",
			"H&M Group Sustainability Report",
			"H&M Foundation",
			"Customer Service",
			"Student Discount",
			"Find a store",
			"Newsletter",
			"Download iOS",
			"Download Android",
			"Enable high-contrast mode",
			"READ H&M MAGAZINE",
			"Read The Story",
			"Career at H&M",
			"About H&M",
			"Press",
			"Investor Relations",
			"Corporate Governance",
			"Legal & Privacy",
			"Contact",
			"Gift Card",
			"CA Supply Chains Act",
			"California Privacy Rights",
			"READ MORE",
			"Facebook",
			"Twitter",
			"Instagram",
			"Youtube",
			"Pinterest",
			"H&M",
			"United States",
			"Privacy Notice",
			"The Fall Home Refresh",
			"Rattan & Straw",
			"Shades of Light",
			"Homewear",
		]
	)

	stop_cats = set(["home", "customer-service"])

	links = {}
	for a in soup.find_all("a", href=True):
		cat = a.text.strip()
		if cat == "" or cat in stopwords:
			continue
		link = a["href"]

		# avoid internal links
		if not link.startswith("#"):
			if link.startswith("/"):
				link = "https://www2.hm.com" + link

			if link not in links.values():
				s_link = link.split("/")
				# if not the homepage (e.g.,https://www2.hm.com/en_us/women.html)
				if len(s_link) > 5:
					# if not apart of a prohibited category
					if (s_link[-3] not in stop_cats) and (s_link[-2] not in stop_cats):
						# print('cat: ',cat)
						# print('link: ',link)
						links[cat] = link
						# print('\n')

	print("get categories")
	print("--- %s seconds ---" % (time.time() - start_time), "\n")

	return links


def get_items(cat_links):
	"""get links to each item currently for sale on the hm us page"""

	item_links = {}
	start_time = time.time()

	# ---- load all the products in the category ----

	# instantiate webdriver
	options = prep_driver(user_agent)
	driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
	driver.maximize_window()

	# keep clicking on load more until all products have been loaded (i.e., until load more button no longer exists)

	# ---- get the contents of the category page ----
	for URL in list(cat_links.values()):
		print(URL)

		driver.get(URL)

		# locate the load more button, if none exists this isn't a product page so continue to next URL
		load_more = driver.find_elements_by_css_selector('button.button.js-load-more')

		# if no load more button found, move onto a product page
		if load_more == []:
			continue

		# click on load more button once clickable
		try:
			# click until there is an exception (exception will happen when button no longer exists)
			while True:
				WebDriverWait(driver, 5).until(
					EC.element_to_be_clickable((By.CSS_SELECTOR, "button.button.js-load-more"))
				).click()
				# driver.execute_script("arguments[0].scrollIntoView();",load_more)
				# driver.execute_script("arguments[0].click();",load_more)

				# path = '//*[@id="page-content"]/div/div[2]/div[2]/button'
				# WebDriverWait(driver, 5).until(
				# 	EC.element_to_be_clickable((By.XPATH, path))
				# ).click()

				# TODO: check the embedded data structures

		except TimeoutError:
			driver.quit()
		except Exception as e:
			print(e)
			print('no load more button found, moving onto request')
			pass


		print("making request")
		# get the contents of the page
		response = requests.get(URL, headers={"User-Agent": user_agent})
		if response.status_code != http.client.OK:
			logging.error(f"Error retrieving {URL}: {response.status_code}")
			continue

		# create BeautifulSoup obj and find product listings
		soup = BeautifulSoup(response.content.decode("utf-8"), "lxml")
		products = soup.find("ul", {"class": "products-listing"})
		print("products: ", products, "\n")

		# iterate through each product and append to dict of items
		for li in products.find_all("li", class_=re.compile(".*product-item")):
			print("li: ", li)
			for a in li.find_all("a", class_="link"):
				print("a: ", a)
				# get the links and name of each product
				link = "https://www2.hm.com/" + a.get("href")
				name = a.get_text()

				if (link not in item_links.values()) and (
					name not in item_links.keys()
				):
					# if item is not already in the dict and if the name is not taken, append it to the dict
					print("name: ", name)
					print("link: ", link)
					item_links[name] = link
				else:
					# hm reuses the same name for multiple products, so append 2 random ints to the name of a product if the name is already taken
					if name in item_links.keys():
						name = (
							name
							+ "-"
							+ str(random.randint(0, 9))
							+ str(random.randint(0, 9))
						)

						print("name: ", name)
						print("link: ", link)
						item_links[name] = link
					# if the link is already in the dict, then the same piece appears in multiple categories. Move on to the next item.

		pprint(item_links, indent=4)
		print(len(item_links))

		print("get items")
		print("--- %s seconds ---" % (time.time() - start_time), "\n")
		# TODO: break is for testing purposes, remove for production
		break


def get_item_data(item_links):
	pass


def post_db(item_data):
	pass


if __name__ == "__main__":

	cat_links = get_categories()
	item_links = get_items(cat_links)
	# item_data = get_item_data(item_links)

	# post_db(item_data)
