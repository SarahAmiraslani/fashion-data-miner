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
from time import sleep
from bs4 import BeautifulSoup

import http.client
import logging

from utilities.helper_functions import get_user_agent, prep_driver, saveList, loadList
import os
import pandas as pd
import numpy as np

# set user agent to imitate browser requests
user_agent: str = get_user_agent()

def get_sitemap_urls():
	"""
	Scrapes DollsKill main sitemap page for all sub-sitemap urls

	Returns:
	sitemap_list (list): list of sitemap urls (str) of form 'http://...xml'
		these urls can be used to scrape for product urls
	"""
	main_sitemap_url = "https://www.dollskill.com/sitemap.xml"
	start_time = time.time()
	options = prep_driver(user_agent)
	driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
	driver.get(main_sitemap_url)
	sleep(3)
	page = driver.page_source
	soup = BeautifulSoup(page, 'xml')
	sitemap_els = soup.find_all('sitemap') # div:opened holds all sitemap link elements
	sitemap_urls = [sitemap.find('loc').text for sitemap in sitemap_els]
	driver.close()
	print('Seconds to get all sitemap urls:', time.time() - start_time)
	return sitemap_urls # list of all sub-sitemap urls


def get_init_product_df(sitemap_list):
	"""
	Gets initial product information: `display_name`, `product_url`, `image_links`
	for ALL products on DollsKill website

	Parameters:
	sitemap_list (list): list of sitemap urls (str)

	Returns:
	init_df (pandas dataframe): initial dataframe holding product information
	"""
	start_time = time.time()
	options = prep_driver(user_agent)
	driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
	init_df = pd.DataFrame(columns = ['display_name', 'product_url', 'image_links'])
	for sitemap_url in sitemap_list:
		init_df = init_df.append(get_url_helper(sitemap_url))
	driver.close()
	print('Total seconds to scrape for all product urls:', time.time() - start_time)

	return init_df

def get_url_helper(sitemap_url):
	"""
	Helper function for get_init_product_df() function;
	Scrapes a given sub sitemap url for all of the initial product information:
	 `display_name`, `product_url`, `image_links`

	Parameters:
	sitemap_url (str): sub sitemap link of form text/string 'http://....xml'

	Returns:
	df (pandas dataframe): initial product information for the inputted sitemap_url
	"""
	start_time = time.time()
	options = prep_driver(user_agent)
	driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
	driver.get(sitemap_url)
	page = driver.page_source
	soup = BeautifulSoup(page, 'xml')
	url_elements = soup.find_all('url')
	df = pd.DataFrame(columns = ['display_name', 'product_url', 'image_links'])
	for url_el in url_elements:
		poss_link_el = url_el.find('loc')
		# print('current link testing:', poss_link_el.text)
		if (poss_link_el is not None):
			# there is a loc element -> there is a url
			img_els = url_el.find_all('image:image')
			if (len(img_els) != 0): # considers all links without images as non-products
				# the image tag exists & the current link scraping is a product
				product_url = poss_link_el.text
				display_name = img_els[0].find('image:title').text
				image_links = [img.find('image:loc').text for img in img_els]
				row = {'display_name' : display_name, 'product_url': product_url, 'image_links' : image_links}
				df = df.append(row, ignore_index = True)
			# else:
				# print('image tag does not exitst, this link is not a product:', poss_link_el.text)
	print('This current sitemap took', time.time() - start_time, 'seconds to scrape')
	driver.close()
	return df

def get_product_info(init_df):
	for _, row in init_df.iterrows():
		url = row['product_url']
		options = prep_driver(user_agent)
		driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
		try:
			driver.get(url)
		except Exception as e:
			print('Uh oh, exception occurred! Could not get url:', e)
			## TODO

		sizes, availabilities, prices, descriptions, brands = [], [], [], [], []


		# get `size`:
		try:
			size_path = '//main/div/div[1]/div/div/div/div[2]/div/div[7]/select/option'
			size_els = driver.find_elements(By.XPATH, size_path)
			size = []
			if len(size_els) == 1:
				# one size item
				size.append(size_els[0].text)
			else:
				# multiple sized item
				# regex only extracts size & not whether out of stock
				size = [re.match('^[^-]*[^ -]', el.text).group(0) for el in size_els if 'select a size' not in el.text.lower()]
			sizes.append(size) # DONE
		except Exception as e:
			# append None type if cannot find by xpath
			print('Uh oh, exception occurred! Could not get size:', e)
			sizes.append(str(type(e)))

		# get `price`: current price (sale price if on sale)
		try:
			price_path = '//main/div/div[1]/div/div/div/div[2]/div/div[3]/div/span'
			price_els = driver.find_elements(By.XPATH, price_path)
			price = re.search('[-0-9.,]+', price_els[-1].text).group()
			prices.append(price) # DONE
		except Exception as e:
			# price = None type if could not find by xpath
			print('Uh oh, exception occurred! Could not get price:', e)
			prices.append(str(type(e)))


		# get `availability`: if sold out
		try:
			avail_path = '//main/div/div[1]/div/div/div/div[1]/div/div/div/div[2]/div'
			avail_el = driver.find_element(By.XPATH, avail_path)
			availability = 1
			if avail_el.text.lower() == 'sold out':
				availability = 0
			availabilities.append(availability) # DONE
		except Exception as e:
			print('Uh oh, exception occurred! Could not get availability:', e)
			availabilities.append(str(type(e)))

		# get everything drop dropdown buttons
		# 1. find "Description" button
		try:
			buttons_xpath = '//div[1]/main/div/div[1]/div/div/div/div[2]/div/div[10]/'
			descrip_xpath = buttons_xpath + 'div[1]'
			descrip_button = driver.find_element(By.XPATH, descrip_xpath)
			driver.execute_script("arguments[0].scrollIntoView();", descrip_button)
			driver.execute_script("arguments[0].click();", descrip_button)
			description = descrip_button.find_element(By.TAG_NAME, 'p').text
			descriptions.append(description)
		except Exception as e:
			# input None type if cannot find by xpath
			print('Uh oh, exception occurred! Could not get description:', e)
			descriptions.append(str(type(e)))

		# get `brand`
		try:
			brand_path = '//main/div/div[1]/div/div/div/div[2]/div/div[1]/a'
			brand_el = driver.find_element(By.XPATH, brand_path)
			brand = 'Dolls Kill' # default brand
			if len(brand_el.text) != 0:
				brand = brand_el.text
			brands.append(brand)
		except Exception as e:
			print('Uh oh, exception occurred! Could not get brand:', e)
			brands.append(str(type(e)))

		# 2. Find "Details" button (color possibly, materials)
		# details_path = buttons_xpath + 'div[2]'
		# details_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, details_path)))
		# details_button.click()
		# bullet_pt_els = details_button.find_elements(By.XPATH, './/ul/li/span')
		# for bullet in bullet_pt_els:
		# 	print(bullet.text)

		nrows = init_df.shape[0]
		# Default data:
		gender = ['Women'] * nrows
		secondhand = [0] * nrows
		shipping_from = [np.NaN] * nrows
		scrapped_date = [str(datetime.today().date())] * nrows
		retailer = ['Dolls Kill'] * nrows
		currency = ['USD'] * nrows

	return pd.Series({'size' : sizes, 'price' : prices, 'description' : descriptions,
					'brand' : brands, 'availability' : availabilities, 'gender' : gender,
					'secondhand' : secondhand, 'shipping_from' : shipping_from,
					'scrapped_date' : scrapped_date, 'retailer' : retailer, 'currency' : currency})

def save_dollskill_brands():
	"""
	Get & save all the brands on Dolls Kill
	"""
	brand_list_url = 'https://www.dollskill.com/shop-brands'
	options = prep_driver(user_agent)
	driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
	driver.get(brand_list_url)
	brand_sections_path = '//main/div/div[1]/div/div[2]/div'
	section_els = driver.find_elements(By.XPATH, brand_sections_path)
	brand_list = []
	for section in section_els:
		brand_els = section.find_elements(By.XPATH, './/ul/p/a/span')
		brand_list.extend([el.text for el in brand_els])
	brand_list = np.array(brand_list)
	save_path = os.path.join(os.getcwd(), 'data', 'dollskill_brands.npy')
	saveList(brand_list, save_path)

def test():
	print('compiled!')

def update_url_df():
	sitemap_urls = get_sitemap_urls() # 1
	product_df = get_init_product_df(sitemap_urls) # 2
	path = os.path.join(os.getcwd() + '\data') # 3a
	product_df.to_csv(path + '\dollskill_urls.csv', index=False) # 3b

def scrape_product_info():
	init_df = pd.read_csv('data\dollskill_urls.csv')
	init_df[['size', 'price', 'description', 'brand', 'availability',
	'gender', 'secondhand', 'shipping_from', 'scrapped_date', 'retailer',
	'currency']] = get_product_info(init_df)
	path = os.path.join(os.getcwd() + '\data')
	# print(path)
	init_df.to_csv(path + '\dollskill_init.csv', index=False)

	# need to scrape from dollskill_init.csv:
	# 1. materials
	# 2. color
	# 3. high level
	# 4. low level
	# maybe: style --


if __name__ == "__main__":
	# update_url_df() # step 1
	scrape_product_info() # step 2


	# test()
	# save_dollskill_brands()
