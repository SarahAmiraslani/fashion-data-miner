from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup

# utilities
import requests
import csv

# frontend modules
from tqdm import tqdm

# user defined functions
from helper_functions import *


# Get all URLs and remove NoneType values
cat_list = get_cat('https://en.lesrecuperables.com')
cat_list = [string for string in cat_list if string]

# Filter URLs
substring = ['/Collections/']
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
    path = '/Users/ericmestiza/Downloads/chromedriver'
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument(f'user-agent={user_agent}')
    driver = webdriver.Chrome(executable_path=path, options=options)
    driver.get(cat_url)

    # Name of the category
    cat_name = driver.find_element_by_class_name('section-header__title').text

    if cat_name not in cat_dict:
        driver.get(cat_url)

        # Assign values for container of all items, invdividual items, item URL
        all_items = driver.find_element_by_xpath('//*[@id="CollectionSection"]/div[2]')
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
les_url_list = []

for i in cat_dict_load:
    l = cat_dict_load[i]
    for j in range(len(l)):
        les_url_list.append(l[j])

# Remove duplicate urls
les_url_list = list(set(les_url_list))

# Remove NoneType values and uneccssary items
les_url_list = [string for string in les_url_list if string]
substring = ['/Collections/tot-accessories']
les_url_list = [string for string in les_url_list if all(sub not in string for sub in substring)]

# print(les_url_list)
# print(len(les_url_list))

url_list = []

# Scraper function
def les_scraper(les_url_list, url_list):

    # Define empty lists to store results and log failed URLs
    failed = []
    results = []

    for les_url in tqdm(les_url_list):

        if les_url not in url_list:
            # Empty dictionary to store output
            les_results = {}

            # Beautiful soup driver
            HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}
            content = requests.get(les_url, headers=HEADERS)
            soup = BeautifulSoup(content.text, 'html.parser')

            # Selenium driver
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
            path = '/Users/ericmestiza/Downloads/chromedriver'
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument(f'user-agent={user_agent}')
            driver = webdriver.Chrome(executable_path=path, options=options)
            driver.get(les_url)

            try:
                # Product name
                les_name = soup.find('h1', {'class': 'h2 product-single__title'}).get_text(strip=True).strip('.')
                les_results['Name'] = les_name

                # Product material
                # Click "Material" button
                buttonMaterial = driver.find_element_by_xpath('/html/body/div[2]/div/main/div[1]/div/div/div/div/div[2]/div/div[5]/button[1]')
                buttonMaterial.click()

                les_material = {el.text.strip(',').strip('Composition:').strip('composition:') for el in driver.find_elements_by_xpath('//*[@id="Product-content--content1"]/div/ul/li[2]')}
                les_results['Material'] = les_material

                # Product color
                les_color = []

                color = soup.find('span', {'class': 'variant__label-info'}).get_text(strip=True).strip('—')
                les_color.append(color)
                les_results['Color'] = les_color

                # Product price
                les_price = soup.find('span', {'class': 'product__price limoniapps-discountninja-productprice'}).get_text(strip=True)
                les_results['Price'] = les_price

                # Product URL
                les_results['URL'] = les_url

                # Product image
                les_image = []

                for img in soup.find('div', {'class': 'product__thumb-item'}).find_all('a'):
                    les_image.append('https:' + img['href'])

                les_results['Image'] = les_image

                # Dictionary of color: image URL
                color_image_dict = {}

                for color in les_color:
                    for img in les_image:
                        color_image_dict[color] = img

                les_results['Color:Image'] = color_image_dict

                # Product description
                les_description = [desc.get_text(strip=True) for desc in soup.find('div', {'class': 'product-single__description rte'}).find_all('p')]
                les_results['Description'] = les_description

                # print(les_results)

                # Add dictionary output to list
                results.append(les_results)

            # TODO: (sarah) I don't think you need the conditional statements here, unless you want to write the kind of error it is to the file
            except (NoSuchElementException, AttributeError, TypeError):
                if NoSuchElementException:
                    failed.append(les_url)
                elif AttributeError:
                    failed.append(les_url)
                elif TypeError:
                    failed.append(les_url)
                pass

            with open('les_table.csv', mode='w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=['Name', 'Material', 'Color', 'Price', 'URL', 'Image', 'Color:Image', 'Description'])
                writer.writeheader()
                writer.writerows(results)

            with open('failed_les.txt', mode='w') as txt_file:
                for row in failed:
                    txt_file.write(str(row) + '\n')

# Scraper
les_scraper(les_url_list, url_list)
