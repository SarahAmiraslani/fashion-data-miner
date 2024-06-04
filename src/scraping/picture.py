# Web driver and html parsing
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import re

# Utilities
import requests
import csv
from tqdm import tqdm

# User defined
from utilities.scrapping_utility import *

# Save path to local chrome driver (install if not already)
cd_path = ChromeDriverManager().install()

# Get all URLs and remove NoneType values
men_list = get_cat(
    'https://www.picture-organic-clothing.com/collection/en/68-men', cd_path)
men_list = [string for string in men_list if string]

# Remove duplicate URLs
men_list = list(set(men_list))

# Get all URLs and remove NoneType values
women_list = get_cat(
    'https://www.picture-organic-clothing.com/collection/en/3-women', cd_path)
women_list = [string for string in women_list if string]

# Remove duplicate URLs
women_list = list(set(women_list))

# Merge all lists
picture_url_list = men_list + women_list

# Remove duplicate urls
picture_url_list = list(set(picture_url_list))

# Remove NoneType values and uneccssary items
picture_url_list = [string for string in picture_url_list if string]
substring = ['book', 'wallet']
picture_url_list = [string for string in picture_url_list if all(
    sub not in string for sub in substring)]

# print(picture_url_list)
# print(len(picture_url_list))

url_list = []

# Scraper function


def picture_scraper(picture_url_list, url_list, cd_path):

    # Define empty lists to store results and log failed URLs
    failed = []
    results = []

    for picture_url in tqdm(picture_url_list):
        if picture_url not in url_list:
            # Empty dictionary to store output
            picture_results = {}

            # Beautiful soup driver
            HEADERS = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}
            content = requests.get(picture_url, headers=HEADERS)
            soup = BeautifulSoup(content.text, 'html.parser')

            # Selenium driver
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
            # path = '/Users/ericmestiza/Downloads/chromedriver'
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument(f'user-agent={user_agent}')
            driver = webdriver.Chrome(executable_path=cd_path, options=options)
            driver.get(picture_url)

            try:
                # Product name
                picture_name = soup.find(
                    'h1', {'class': 'm-product__name'}).get_text(strip=True)
                picture_results['Name'] = picture_name

                # Product material
                picture_material = {el.text.strip('/') for el in driver.find_elements_by_xpath(
                    '//*[@id="product"]/div[1]/div/div/div[2]/div[1]/div/div[1]/div/div/div[2]/div[1]/p')}
                picture_results['Material'] = picture_material

                # Product color
                picture_color = []

                for color in soup.find('ul', {'class': 'c-product-attribute-color'}).find_all('a'):
                    picture_color.append(color['title'])

                picture_results['Color'] = picture_color

                # Product price
                picture_price = soup.find(
                    'span', {'class': 'price'}).get_text(strip=True)
                picture_results['Price'] = picture_price

                # Product URL
                picture_results['URL'] = picture_url

                # Product image
                picture_image = []

                for img in soup.find_all('div', {'data-zoom': True}):
                    picture_image.append(img['data-zoom'])

                picture_results['Image'] = picture_image

                # Dictionary of color: image URL
                color_image_dict = {}

                for color in picture_color:
                    for img in picture_image:
                        color_image_dict[color] = img

                picture_results['Color:Image'] = color_image_dict

                # Product description
                picture_description = [desc.text for desc in driver.find_elements_by_xpath(
                    '//*[@id="product"]/div[1]/div/div/div[2]/div[1]/div/div[2]/div/div/div[2]')]
                picture_results['Description'] = picture_description

                # print(picture_results)

                # Add dictionary output to list
                results.append(picture_results)

            # TODO: (sarah) I don't think you need the conditional statements here, unless you want to write the kind of error it is to the file
            except (NoSuchElementException, AttributeError, TypeError):
                if NoSuchElementException:
                    failed.append(picture_url)
                elif AttributeError:
                    failed.append(picture_url)
                elif TypeError:
                    failed.append(picture_url)
                pass

            with open('picture_table.csv', mode='w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=[
                                        'Name', 'Material', 'Color', 'Price', 'URL', 'Image', 'Color:Image', 'Description'])
                writer.writeheader()
                writer.writerows(results)

            with open('failed_picture.txt', mode='w') as txt_file:
                for row in failed:
                    txt_file.write(str(row) + '\n')


# Scraper
picture_scraper(picture_url_list, url_list, cd_path)
