# Web driver and html parsing
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup

# Utilities
import requests
import csv
from tqdm import tqdm

# User defined
from utilities.scrapping_utility import *

# Save path to local chrome driver (install if not already)
cd_path = ChromeDriverManager().install()

# Get all URLs and remove NoneType values
cat_list = get_cat('https://www.thisisaday.com', cd_path)
cat_list = [i for i in cat_list if i]

# Filter URLs and removw duplicates
substring = ['collections']
cat_list = [string for string in cat_list if any(
    sub in string for sub in substring)]  # TODO: what is this any doing?
cat_list = list(set(cat_list))

# print(cat_list)
# print(type(cat_list))
# print(len(cat_list))

cat_dict = {}

# Function to extract URLs of all items in each category


def cat_itemize(cat_url, cd_path):

    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument(f'user-agent={user_agent}')
    driver = webdriver.Chrome(executable_path=cd_path, options=options)
    driver.get(cat_url)

    # Name of the category
    cat_name = driver.find_element_by_xpath(
        '//*[@id="app_collections"]/div[2]/div[2]/div[2]/div[1]/div').text

    if cat_name not in cat_dict:
        driver.get(cat_url)

        # Assign values for container of all items, invdividual items, item URL
        all_items = driver.find_element_by_xpath(
            '//*[@id="app_collections"]/div[2]/div[2]/div[2]')
        items = all_items.find_elements_by_tag_name('a')
        cat_items = [item.get_attribute('href') for item in items]
        cat_dict[cat_name] = cat_items

        driver.quit()

    return cat_dict


# Create dictionary where key = category and value = category item urls
for i in range(len(cat_list)):
    cat_dict_load = cat_itemize(cat_list[i], cd_path)

# print(cat_dict_load)
# print(cat_list)

# Join dictionary values (url lists) into one list
aday_url_list = []

for i in cat_dict_load:
    l = cat_dict_load[i]
    for j in range(len(l)):
        aday_url_list.append(l[j])

# Remove duplicate urls
aday_url_list = list(set(aday_url_list))

# Remove uneccssary urls #TODO: what is the point of any here? how does it differ from all? (all is used in some of the other files like vatter.py)
exclude = ['gift-card', 'offset-your']
aday_url_list = [string for string in aday_url_list if any(
    sub not in string for sub in exclude)]

# print(aday_url_list)
# print(len(aday_url_list))

url_list = []

# Scraper function


def aday_scraper(aday_url_list, url_list, cd_path):

    # Define empty lists to store results and log failed URLs
    failed = []
    results = []

    for aday_url in tqdm(aday_url_list):
        if aday_url not in url_list:
            # Empty dictionary to store output
            aday_results = {}

            # Beautiful soup driver
            HEADERS = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}
            content = requests.get(aday_url, headers=HEADERS)
            soup = BeautifulSoup(content.text, 'html.parser')

            # Selenium driver
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
            # path = '/Users/ericmestiza/Documents/chromedriver'
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument(f'user-agent={user_agent}')
            driver = webdriver.Chrome(executable_path=cd_path, options=options)
            driver.get(aday_url)

            try:
                # Product name
                aday_name = driver.find_element_by_xpath(
                    '//*[@id="app_product_info"]/div[1]/h1').text
                aday_results['Name'] = aday_name

                # Product material
                # Click button
                button = driver.find_element_by_xpath(
                    '//*[@id="app_product_info"]/div[9]/div[2]/div[1]')
                driver.execute_script("arguments[0].click();", button)
                aday_material = [el.text for el in driver.find_elements_by_xpath(
                    '//*[@id="app_product_info"]/div[9]/div[2]/div[2]')]
                aday_results['Material'] = aday_material

                # Product color
                aday_color = []
                aday_color.append(driver.find_element_by_xpath(
                    '//*[@id="app_product_info"]/div[4]/div[2]/span').text.strip('COLOR').strip('\n: '))
                aday_results['Color'] = aday_color

                # Product price
                aday_price = driver.find_element_by_xpath(
                    '//*[@id="app_product_info"]/div[1]/div/span').text
                aday_results['Price'] = aday_price

                # Product URL
                aday_results['URL'] = aday_url

                # Product image
                aday_image = []

                for img in soup.find_all('img', {'data-src': True}):
                    aday_image.append('https:' + img['data-src'])

                aday_results['Image'] = aday_image

                # Dictionary of color: image URL
                color_image_dict = {}

                for color in aday_color:
                    for img in aday_image:
                        color_image_dict[color] = img

                aday_results['Color:Image'] = color_image_dict

                # Product description
                aday_description = [desc.text for desc in driver.find_elements_by_xpath(
                    '//*[@id="app_product_info"]/div[8]')]
                aday_results['Description'] = aday_description

                # Add dictionary output to list
                results.append(aday_results)

            # TODO: (sarah) I don't think you need the conditional statements here, unless you want to write the kind of error it is to the file
            except (NoSuchElementException, AttributeError, TypeError):
                if NoSuchElementException:
                    failed.append(aday_url)
                elif AttributeError:
                    failed.append(aday_url)
                elif TypeError:
                    failed.append(aday_url)
                pass

            with open('aday_table.csv', mode='w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=[
                                        'Name', 'Material', 'Color', 'Price', 'URL', 'Image', 'Color:Image', 'Description'])
                writer.writeheader()
                writer.writerows(results)

            with open('failed_aday.txt', mode='w') as txt_file:
                for row in failed:
                    txt_file.write(str(row) + '\n')


# Scraper
aday_scraper(aday_url_list, url_list, cd_path)
