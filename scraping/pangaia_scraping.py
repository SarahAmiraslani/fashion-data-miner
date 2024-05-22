from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
from bs4 import BeautifulSoup
from multiprocessing.pool import Pool
from multiprocessing import current_process
from functools import partial
from tqdm import tqdm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import requests
import re
import itertools
import time
import csv
import concurrent.futures
# Use this instead of local path
from webdriver_manager.chrome import ChromeDriverManager
# path = ChromeDriverManager().install()
drivermanager = ChromeDriverManager().install()

# Function to extract category URLs


def get_cat(full_url):

    # Selenium driver
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'
    # path = '/Users/ericmestiza/Documents/chromedriver'
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument(f'user-agent={user_agent}')
    driver = webdriver.Chrome(
        executable_path=ChromeDriverManager().install(), options=options)
    driver.get(full_url)

    # Find class for tags with URLs to loop through
    elems = driver.find_elements_by_class_name('site-nav__subtitle')
    cat_list = [elem.get_attribute('href') for elem in elems]

    driver.quit()

    return cat_list


# Get all URLs and remove NoneType values
cat_list = get_cat('https://thepangaia.com/collections/men-shop-all')
cat_list = [i for i in cat_list if i]

# Filter URLs
substring = ['men-', 'women-', 'kids-']
cat_list = [string for string in cat_list if any(
    sub in string for sub in substring)]

cat_dict = {}

# Function to extract URLs of all items in each category


def cat_itemize(cat_url):

    global cat_dict

    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'
    # path = '/Users/ericmestiza/Documents/chromedriver'
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument(f'user-agent={user_agent}')
    driver = webdriver.Chrome(executable_path=drivermanager, options=options)
    driver.get(cat_url)

    # Name of the category
    cat_name = driver.find_element_by_xpath(
        '//*[@id="bc-sf-filter-default-toolbar"]/nav/span[2]').text

    if cat_name not in cat_dict:
        driver.get(cat_url)

        # Assign values for container of all items, invdividual items, item URL
        all_items = driver.find_element_by_xpath(
            '/html/body/main/div/div/div/div[2]/div[5]')
        items = all_items.find_elements_by_class_name(
            'bc-sf-filter-product-item-image-link')
        cat_items = [item.get_attribute('href') for item in items]

        cat_dict[cat_name] = cat_items
        driver.quit()

    return cat_dict


# Create dictionary where key = category and value = category item urls
for i in range(len(cat_list)):
    cat_dict_load = cat_itemize(cat_list[i])

# Join dictionary values (url lists) into one list
pangaia_url_list = []

for i in cat_dict_load:
    l = cat_dict_load[i]
    for j in range(len(l)):
        pangaia_url_list.append(l[j])

# Remove duplicate urls
pangaia_url_list = list(set(pangaia_url_list))

# Remove uneccssary items
exclude = ['gift-card', 'notebook']
pangaia_url_list = [string for string in pangaia_url_list if any(
    sub not in string for sub in exclude)]

url_list = []

# Scraper function


def pangaia_scraper(pangaia_url_list, url_list):

    # Define empty lists to store results and log failed URLs
    failed = []
    results = []

    for pangaia_url in tqdm(pangaia_url_list):
        if pangaia_url not in url_list:
            # Empty dictionary to store output
            pangaia_results = {}

            # Beautiful soup driver
            HEADERS = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}
            content = requests.get(pangaia_url, headers=HEADERS)
            soup = BeautifulSoup(content.text, 'html.parser')

            # Selenium driver
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
            path = '/Users/ericmestiza/Documents/chromedriver'
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument(f'user-agent={user_agent}')
            driver = webdriver.Chrome(
                executable_path=drivermanager, options=options)
            driver.get(pangaia_url)

            try:
                # Product name
                pangaia_name = soup.find(
                    'span', {'class': 'breadcrumb__item'}).get_text()
                pangaia_results['Name'] = pangaia_name

                # Product material
                # Click "Material" button
                buttonMaterial = driver.find_element_by_xpath(
                    '//*[@id="shopify-section-product-template"]/div/div[1]/div[2]/div/div[2]/ul/li[1]/button')
                driver.execute_script("arguments[0].click();", buttonMaterial)

                pangaia_material = [el.text for el in driver.find_elements_by_xpath(
                    '//*[@id="product-info-modal"]/div/div/div[2]/div/div/div/div[1]/p[2]')]
                pangaia_results['Material'] = pangaia_material

                # Product color
                pangaia_color = []
                # Click "Color" button
                buttonColor = driver.find_element_by_xpath(
                    '//*[@id="OptionSelector-Color"]/div/button')
                driver.execute_script("arguments[0].click();", buttonColor)

                for color in soup.find('span', {'class': 'product-form__legend'}).find_all('span', {'class': 'swatch__label swatch__label--colour'}):
                    pangaia_color.append(color.get_text().strip())

                pangaia_results['Color'] = pangaia_color

                # Product price
                pangaia_price = soup.find(
                    'span', {'data-price': True}).get_text().strip()
                pangaia_results['Price'] = pangaia_price

                # Product URL
                pangaia_results['URL'] = pangaia_url

                # Product image
                pangaia_image = []

                for img in soup.find('div', {'class': 'template-product__gallery'}).find_all('div', {'data-zoom': True}):
                    pangaia_image.append('https:' + img['data-zoom'])

                pangaia_results['Image'] = pangaia_image

                # Dictionary of color: image URL
                color_image_dict = {}

                for color in pangaia_color:
                    for img in pangaia_image:
                        color_image_dict[color] = img

                pangaia_results['Color:Image'] = color_image_dict

                # Product description
                pangaia_description = [desc.text for desc in driver.find_elements_by_xpath(
                    '/html/body/main/div/div/div[1]/div[2]/div/div[1]/div[2]/p')]
                pangaia_results['Description'] = pangaia_description

                # Add dictionary output to list
                results.append(pangaia_results)

            except (NoSuchElementException, AttributeError, TypeError):
                if NoSuchElementException:
                    failed.append(pangaia_url)
                elif AttributeError:
                    failed.append(pangaia_url)
                elif TypeError:
                    failed.append(pangaia_url)
                pass

            with open('pangaia/pangaia_table.csv', mode='w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=[
                                        'Name', 'Material', 'Color', 'Price', 'URL', 'Image', 'Color:Image', 'Description'])
                writer.writeheader()
                writer.writerows(results)

            with open('pangaia/failed_pangaia.txt', mode='w') as txt_file:
                for row in failed:
                    txt_file.write(str(row) + '\n')


# Scraper
pangaia_scraper(pangaia_url_list, url_list)
