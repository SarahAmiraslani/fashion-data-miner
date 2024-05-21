# web driver and html parsing
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import re

# utilities
import requests
import csv
from tqdm import tqdm

# user defined
from utilities.helper_functions import *


# Get all URLs and remove NoneType values
cat_list = get_cat('https://www.outerknown.com')
cat_list = [string for string in cat_list if string]

# Filter URLs
substring = ['/collections/']
cat_list = [string for string in cat_list if all(sub in string for sub in substring)]

# Remove duplicate URLs
cat_list = list(set(cat_list))

# print(cat_list)
# print(len(cat_list))

cat_dict = {}

# Function to extract URLs of all items in each category
def cat_itemize(cat_url):

    # Selenium driver
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'
    path = '/Users/ericmestiza/Documents/chromedriver'
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument(f'user-agent={user_agent}')
    driver = webdriver.Chrome(executable_path=path, options=options)
    driver.get(cat_url)

    # Name of the category
    cat_name = driver.find_element_by_tag_name('h1').text

    if cat_name not in cat_dict:
        driver.get(cat_url)

        # Assign values for container of all items, invdividual items, item URL
        all_items = driver.find_element_by_xpath('//*[@id="MainContent"]/div/div/div[2]/div')
        items = all_items.find_elements_by_tag_name('a')
        cat_items = [item.get_attribute('href') for item in items]
        cat_dict[cat_name] = cat_items

        driver.quit()

    return cat_dict

# Create dictionary where key = category and value = category item urls
for i in range(len(cat_list)):
    cat_dict_load = cat_itemize(cat_list[i])

# print(cat_dict_load)

# Join dictionary values (url lists) into one list
outerknown_url_list = []

for i in cat_dict_load:
    l = cat_dict_load[i]
    for j in range(len(l)):
        outerknown_url_list.append(l[j])

# Remove duplicate urls
outerknown_url_list = list(set(outerknown_url_list))

# print(outerknown_url_list)
# print(len(outerknown_url_list))

# Remove uneccssary items
outerknown_url_list = [string for string in outerknown_url_list if string]
substring = ['products/gift-card', 'accessories/products', 'collections/shop-all']
outerknown_url_list = [string for string in outerknown_url_list if all(sub not in string for sub in substring)]

# print(outerknown_url_list)
# print(len(outerknown_url_list))

url_list = []

# Scraper function
def outerknown_scraper(outerknown_url_list, url_list):

    # Define empty lists to store results and log failed URLs
    failed = []
    results = []

    for outerknown_url in tqdm(outerknown_url_list):
        if outerknown_url not in url_list:
            # Empty dictionary to store output
            outerknown_results = {}

            # Beautiful soup driver
            HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}
            content = requests.get(outerknown_url, headers=HEADERS)
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
            driver = webdriver.Chrome(executable_path=path, options=options)
            driver.get(outerknown_url)

            try:
                # Product name
                outerknown_name = soup.find('h1', {'class': 'product-detail__title h3'}).get_text()
                outerknown_results['Name'] = outerknown_name

                # Product material
                outerknown_material = {el.text for el in driver.find_elements_by_xpath('//*[@id="shopify-section-product"]/div/section[2]/div/div/div[3]/div/p[1]')}
                outerknown_results['Material'] = outerknown_material

                # Product color
                outerknown_color = []

                for color in soup.find('div', {'class': 'dots dots--expanded dots--medium'}).find_all('a', {'class': 'dot dot--solid'}):
                    outerknown_color.append(color['data-color'])

                outerknown_results['Color'] = outerknown_color

                # Product price
                outerknown_price = soup.find('div', {'class': 'product-price-wrapper h4'}).find('span', {'flow-default': True}).get_text().strip()
                outerknown_results['Price'] = outerknown_price

                # Product URL
                outerknown_results['URL'] = outerknown_url

                # Product image
                outerknown_image = []

                for img in soup.find('div', {'class': 'product-detail__form-col--left col-sm-7 col-md-7'}).find_all('img', {'data-product-image-url': True}):
                    outerknown_image.append('https:' + img['data-product-image-url'])
                # outerknown_image = soup.find('div', {'class': 'hidden-xs ProductGallery__featured'}).find('a', {'href': True})
                # outerknown_image = ['https:' + outerknown_image['href']]

                outerknown_results['Image'] = outerknown_image

                # Dictionary of color: image URL
                color_image_dict = {}

                for color in outerknown_color:
                    for img in outerknown_image:
                        color_image_dict[color] = img

                outerknown_results['Color:Image'] = color_image_dict

                # Product description
                outerknown_description = [desc.text for desc in driver.find_elements_by_xpath('//*[@id="shopify-section-product"]/div/section[2]/div/div/div[1]/div')]
                outerknown_results['Description'] = outerknown_description

                # print(outerknown_results)

                # Add dictionary output to list
                results.append(outerknown_results)

            except (NoSuchElementException, AttributeError, TypeError):
                if NoSuchElementException:
                    failed.append(outerknown_url)
                elif AttributeError:
                    failed.append(outerknown_url)
                elif TypeError:
                    failed.append(outerknown_url)
                pass

            with open('outerknown_table.csv', mode='w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=['Name', 'Material', 'Color', 'Price', 'URL', 'Image', 'Color:Image', 'Description'])
                writer.writeheader()
                writer.writerows(results)

            with open('failed_outerknown.txt', mode='w') as txt_file:
                for row in failed:
                    txt_file.write(str(row) + '\n')

# Scraper
outerknown_scraper(outerknown_url_list, url_list)

# outerknown_df = pd.read_csv('outerknown/outerknown_table.csv')
# print(outerknown_df)
