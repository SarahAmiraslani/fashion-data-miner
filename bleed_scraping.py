from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
from bs4 import BeautifulSoup
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
from webdriver_manager.chrome import ChromeDriverManager

# Function to extract category URLs
def get_cat(full_url):

    # Selenium driver
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument(f'user-agent={user_agent}')
    driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
    driver.get(full_url)

    # Find class for tags with URLs to loop through
    elems = driver.find_elements_by_tag_name('a')
    cat_list = [elem.get_attribute('href') for elem in elems]

    driver.quit()

    return cat_list

# Get all URLs and remove NoneType values
cat_list = get_cat('https://www.bleed-clothing.com/english')
cat_list = [i for i in cat_list if i]

# Filter URLs
substring = ['shop-men', 'shop-women', 'accessories']
cat_list = [string for string in cat_list if any(sub in string for sub in substring)]

# print(cat_list)
# print(len(cat_list))

cat_dict = {}

# Function to extract URLs of all items in each category
def cat_itemize(cat_url):

    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument(f'user-agent={user_agent}')
    driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
    driver.get(cat_url)

    # Name of the category
    cat_name = driver.find_element_by_xpath('//*[@id="top"]/body/div[2]/div/div[4]/div/div[2]/div/div[1]/div/div[1]/h1').text

    if cat_name not in cat_dict:
        driver.get(cat_url)

        # Assign values for container of all items, invdividual items, item URL
        all_items = driver.find_element_by_xpath('//*[@id="top"]/body/div[2]/div/div[4]/div/div[2]/div/div[1]/div/div[2]/div[1]')
        items = all_items.find_elements_by_class_name('product-image')
        cat_items = [item.get_attribute('href') for item in items]
        cat_dict[cat_name] = cat_items

        driver.quit()

    return cat_dict

# Create dictionary where key = category and value = category item urls
for i in range(len(cat_list)):
    cat_dict_load = cat_itemize(cat_list[i])

# print(cat_dict_load)

# Join dictionary values (url lists) into one list
bleed_url_list = []

for i in cat_dict_load:
    l = cat_dict_load[i]
    for j in range(len(l)):
        bleed_url_list.append(l[j])

# Remove duplicate urls
bleed_url_list = list(set(bleed_url_list))

# Remove uneccssary items
exclude = ['digital-voucher']
bleed_url_list = [string for string in bleed_url_list if any(sub not in string for sub in exclude)]

# print(bleed_url_list)
# print(len(bleed_url_list))


url_list = []

# Scraper function
def bleed_scraper(bleed_url_list, url_list):

    # Define empty lists to store results and log failed URLs
    failed = []
    results = []

    for bleed_url in tqdm(bleed_url_list):
        if bleed_url not in url_list:
            # Empty dictionary to store output
            bleed_results = {}

            # Beautiful soup driver
            HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}
            content = requests.get(bleed_url, headers=HEADERS)
            soup = BeautifulSoup(content.text, 'html.parser')

            # Selenium driver
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument(f'user-agent={user_agent}')
            driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
            driver.get(bleed_url)

            try:
                # Product name
                bleed_name = soup.find('h1', {'class': 'product-name-h1'}).get_text()
                bleed_results['Name'] = bleed_name

                # Product material
                bleed_material = [el.text for el in driver.find_elements_by_xpath('//*[@id="product_addtocart_form"]/div[2]/div[2]/div/div[5]/div')]
                bleed_results['Material'] = bleed_material

                # Product color
                bleed_color = []

                for color in soup.find('ul', {'style': 'list-style-type:disc; margin-left: 25px;'}).find_all('li')[1]:
                    bleed_color.append(color.strip('Color:').strip())

                bleed_results['Color'] = bleed_color

                # Product price
                bleed_price = soup.find('div', {'class': 'price-box'}).find('span', {'class': 'price'}).get_text().strip()
                bleed_results['Price'] = bleed_price

                # Product URL
                bleed_results['URL'] = bleed_url

                # Product image
                bleed_image = []

                for img in soup.find_all('img', {'data-rsmainimg': True}):
                    bleed_image.append(img['data-rsmainimg'])

                bleed_results['Image'] = bleed_image

                # Dictionary of color: image URL
                color_image_dict = {}

                for color in bleed_color:
                    for img in bleed_image:
                        color_image_dict[color] = img

                bleed_results['Color:Image'] = color_image_dict

                # Product description
                bleed_description = [desc.text for desc in driver.find_elements_by_xpath('//*[@id="top"]/body/div[2]/div/div[4]/div/div[2]/div/div/div/div/div[2]/div[2]/div/div/div/div[1]/p[2]')]
                bleed_results['Description'] = bleed_description

                # Add dictionary output to list
                results.append(bleed_results)

            except (NoSuchElementException, AttributeError, TypeError):
                if NoSuchElementException:
                    failed.append(bleed_url)
                elif AttributeError:
                    failed.append(bleed_url)
                elif TypeError:
                    failed.append(bleed_url)
                pass

            with open('bleed_table.csv', mode='w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=['Name', 'Material', 'Color', 'Price', 'URL', 'Image', 'Color:Image', 'Description'])
                writer.writeheader()
                writer.writerows(results)

            with open('failed_bleed.txt', mode='w') as txt_file:
                for row in failed:
                    txt_file.write(str(row) + '\n')


# Scraper
bleed_scraper(bleed_url_list, url_list)
print("yay it ran!")
