# web driver and html parsing
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup

# utilities
import requests
import csv
from tqdm import tqdm

# user defined
from utilities.scrapping_utility import *

# save path to local chrome driver (install if not already)
cd_path = ChromeDriverManager().install()

# Get all URLs and remove NoneType values
men_list = get_cat('https://www.armedangels.com/wo-en/men',cd_path)
men_list = [string for string in men_list if string]

# Remove duplicate URLs
men_list = list(set(men_list))

# Get all URLs and remove NoneType values
women_list = get_cat('https://www.armedangels.com/wo-en/women',cd_path)
women_list = [string for string in women_list if string]

# Remove duplicate URLs
women_list = list(set(women_list))

# Merge all lists
armedangels_url_list = men_list + women_list

# Remove duplicate urls
armedangels_url_list = list(set(armedangels_url_list))

# Remove NoneType value URLs
armedangels_url_list = [string for string in armedangels_url_list if string]

# Filter out unecessary URLs
substring = ['www.armedangels.com/']
armedangels_url_list = [string for string in armedangels_url_list if all(sub in string for sub in substring)]

# Remove items URLs
substring = ['giftcard', 'mailto']
armedangels_url_list = [string for string in armedangels_url_list if all(sub not in string for sub in substring)]

# print(armedangels_url_list)
# print(len(armedangels_url_list))

url_list = []

# Scraper function
def armedangels_scraper(armedangels_url_list, url_list,cd_path):

    # Define empty lists to store results and log failed URLs
    failed = []
    results = []

    for armedangels_url in tqdm(armedangels_url_list):
        if armedangels_url not in url_list:
            # Empty dictionary to store output
            armedangels_results = {}

            # Beautiful soup driver
            HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}
            content = requests.get(armedangels_url, headers=HEADERS)
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
            driver.get(armedangels_url)

            try:
                # Product name
                armedangels_name = soup.find('div', {'class': 'headline'}).get_text(strip=True)
                armedangels_results['Name'] = armedangels_name

                # Product material
                armedangels_material = {soup.find('div', {'class': 'material-text'}).get_text(strip=True)}
                armedangels_results['Material'] = armedangels_material

                # Product color
                armedangels_color = []

                for color in soup.find('div', {'class': 'configurator-options'}).find_all('a'):
                    armedangels_color.append(color['title'])

                armedangels_results['Color'] = armedangels_color

                # Product price
                armedangels_price = soup.find('p', {'class': 'product-price product-detail-price'}).get_text(strip=True)
                armedangels_results['Price'] = armedangels_price

                # Product URL
                armedangels_results['URL'] = armedangels_url

                # Product image
                armedangels_image = []

                for img in soup.find_all('img', {'srcset': True}):
                    armedangels_image.append(img['src'])

                armedangels_results['Image'] = armedangels_image

                # Dictionary of color: image URL
                color_image_dict = {}

                for color in armedangels_color:
                    for img in armedangels_image:
                        color_image_dict[color] = img

                armedangels_results['Color:Image'] = color_image_dict

                # Product description
                armedangels_description = [desc.get_text(strip=True) for desc in soup.find_all('span', {'class': 'properties-value'})]
                armedangels_results['Description'] = armedangels_description

                # print(armedangels_results)

                # Add dictionary output to list
                results.append(armedangels_results)

            # TODO: (sarah) I don't think you need the conditional statements here, unless you want to write the kind of error it is to the file
            except (NoSuchElementException, AttributeError, TypeError):
                if NoSuchElementException:
                    failed.append(armedangels_url)
                elif AttributeError:
                    failed.append(armedangels_url)
                elif TypeError:
                    failed.append(armedangels_url)
                pass

            with open('armedangels/armedangels_table.csv', mode='w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=['Name', 'Material', 'Color', 'Price', 'URL', 'Image', 'Color:Image', 'Description'])
                writer.writeheader()
                writer.writerows(results)

            with open('armedangels/failed_armedangels.txt', mode='w') as txt_file:
                for row in failed:
                    txt_file.write(str(row) + '\n')

# Scraper
armedangels_scraper(armedangels_url_list, url_list,cd_path)
