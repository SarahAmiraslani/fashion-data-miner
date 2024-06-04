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
from utilities.scrapping_utility import *

# save path to local chrome driver (install if not already)
cd_path = ChromeDriverManager().install()

# Get all URLs and remove NoneType values
cat_list = get_cat('https://isto.pt',cd_path)
cat_list = [string for string in cat_list if string]

# Filter URLs
substring = ['collections']
cat_list = [string for string in cat_list if any(sub in string for sub in substring)]

# Remove duplicate URLs
cat_list = list(set(cat_list))

# print(cat_list)
# print(len(cat_list))

cat_dict = {}

# Function to extract URLs of all items in each category
def cat_itemize(cat_url,cd_path):

    # Selenium driver
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15'
    # path = '/Users/ericmestiza/Documents/chromedriver'
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument(f'user-agent={user_agent}')
    driver = webdriver.Chrome(executable_path=cd_path, options=options)
    driver.get(cat_url)

    # Name of the category
    cat_name = driver.find_element_by_xpath('/html/body/main/div[1]/div/div[1]/div').text.split()[0]

    if cat_name not in cat_dict:
        driver.get(cat_url)

        # Assign values for container of all items, invdividual items, item URL
        all_items = driver.find_element_by_tag_name('section')
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
isto_url_list = []

for i in cat_dict_load:
    l = cat_dict_load[i]
    for j in range(len(l)):
        isto_url_list.append(l[j])

# Remove duplicate urls
isto_url_list = list(set(isto_url_list))

# print(isto_url_list)
# print(len(isto_url_list))

# Remove uneccssary items
exclude = ['gift-card', 'tgc']
isto_url_list = [string for string in isto_url_list if any(sub not in string for sub in exclude)]

# print(isto_url_list)
# print(len(isto_url_list))

url_list = []

# Scraper function
def isto_scraper(isto_url_list, url_list):

    # Define empty lists to store results and log failed URLs
    failed = []
    results = []

    for isto_url in tqdm(isto_url_list):
        if isto_url not in url_list:
            # Empty dictionary to store output
            isto_results = {}

            # Beautiful soup driver
            HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}
            content = requests.get(isto_url, headers=HEADERS)
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
            driver.get(isto_url)

            try:
                # Product name
                isto_name = soup.find('h1', {'class': 'f--heading f--heading font-size--xl line-height--8 wd--font-size--xxl wd--line-height--9 m0 mb1'}).get_text()
                isto_results['Name'] = isto_name

                # Product material
                txt = soup.find('div',{'class': 'mt3 rte font-size--sm line-height--4 wd--font-size--m wd--line-height--4'}).find('p').text
                pattern = 'SPECS(.*)\xa0'
                isto_material = re.search(pattern, txt, re.IGNORECASE).group(1)
                isto_results['Material'] = isto_material

                # Product color
                isto_color = []

                for color in soup.find('div', {'id': 'swatch_pswatchdiv'}).find_all('div', {'class': 'swatchy_pcolordiv'}):
                    isto_color.append(color['data-balloon'])

                isto_results['Color'] = isto_color

                # Product price
                isto_price = soup.find('div', {'class': 'font-size--xxl item--price'}).find('span').get_text().strip()
                isto_results['Price'] = isto_price

                # Product URL
                isto_results['URL'] = isto_url

                # Product image
                isto_image = []

                for img in soup.find('div', {'class': 'product-flickity__slides pb3 md--up--mtn2 md--up--flex md--up--flex--column'}).find_all('a', {'href': True}):
                    isto_image.append('https:' + img['href'])

                isto_results['Image'] = isto_image

                # Dictionary of color: image URL
                color_image_dict = {}

                for color in isto_color:
                    for img in isto_image:
                        color_image_dict[color] = img

                isto_results['Color:Image'] = color_image_dict

                # Product description
                txt2 = soup.find('div',{'class': 'mt3 rte font-size--sm line-height--4 wd--font-size--m wd--line-height--4'}).find('p').text.strip('\xa0')
                pattern2 = 'OVERVIEW(.*)SPECS'

                isto_description = re.search(pattern2, txt2, re.IGNORECASE).group(1)
                isto_results['Description'] = isto_description

                # print(isto_results)

                # Add dictionary output to list
                results.append(isto_results)

            # TODO: (sarah) I don't think you need the conditional statements here, unless you want to write the kind of error it is to the file
            except (NoSuchElementException, AttributeError, TypeError):
                if NoSuchElementException:
                    failed.append(isto_url)
                elif AttributeError:
                    failed.append(isto_url)
                elif TypeError:
                    failed.append(isto_url)
                pass

            with open('isto_table.csv', mode='w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=['Name', 'Material', 'Color', 'Price', 'URL', 'Image', 'Color:Image', 'Description'])
                writer.writeheader()
                writer.writerows(results)

            with open('failed_isto.txt', mode='w') as txt_file:
                for row in failed:
                    txt_file.write(str(row) + '\n')

# Scraper
isto_scraper(isto_url_list, url_list)
