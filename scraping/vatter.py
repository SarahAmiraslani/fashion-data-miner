# web driver and html parsing
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup

# utilities
import requests
import csv
from tqdm import tqdm

# user defined
from utilities.helper_functions import *

# Save path to local chrome driver (install if not already)
cd_path = ChromeDriverManager().install()

# Get all URLs and remove NoneType values
cat_list = get_cat("https://www.vatter-fashion.com/en")
cat_list = [string for string in cat_list if string]

# Filter URLs and remove duplicates #TODO: for? sarah get a clear understanding of the point of this
substring = ["/collections/"]
cat_list = [string for string in cat_list if all(sub in string for sub in substring)]
cat_list = list(set(cat_list))

# print(cat_list)
# print(len(cat_list))

cat_dict = {}

def cat_itemize(cat_url,cd_path):
    """ Function to extract URLs of all items in each category. Use is specific to the vatter site.

    Args:
        cat_url (str): [description] #TODO: add description

    Returns:
        dict: [description] #TODO: add description
    """

    #TODO: do we want to do what we did with Zara where we randomly choose a user_agent each time? Perhaps that would make the code more robust to scrapping blockers on the website
     # Set ChromeDriver options
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15"
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument(f"user-agent={user_agent}")
    driver = webdriver.Chrome(executable_path=cd_path, options=options)
    driver.get(cat_url)

    # Get name of the category
    cat_name = driver.find_element_by_xpath(
        '//*[@id="shopify-section-collection_page_header"]/section/div/h3'
    ).text

    if cat_name not in cat_dict:
        # TODO: why are we calling driver.get twice on the same cat_url?
        driver.get(cat_url)

        # Assign values for container of all items, invdividual items, item URL
        all_items = driver.find_element_by_xpath('//*[@id="collection-main"]/div[3]')
        items = all_items.find_elements_by_tag_name("a")
        cat_items = [item.get_attribute("href") for item in items]
        cat_dict[cat_name] = cat_items

        driver.quit()

    return cat_dict


# Create dictionary where key = category and value = category item urls
for i in range(len(cat_list)):
    cat_dict_load = cat_itemize(cat_list[i])

# print(cat_dict_load)

# Join dictionary values (url lists) into one list
vatter_url_list = []

for i in cat_dict_load:
    l = cat_dict_load[i]
    for j in range(len(l)):
        vatter_url_list.append(l[j])

# Remove duplicate urls
vatter_url_list = list(set(vatter_url_list))

# Remove NoneType values and uneccssary items
vatter_url_list = [string for string in vatter_url_list if string]
substring = ["products/gutschein", "javascript:void(0);"]
vatter_url_list = [
    string for string in vatter_url_list if all(sub not in string for sub in substring)
]

# print(vatter_url_list)
# print(len(vatter_url_list))

url_list = []

# Scraper function
def vatter_scraper(vatter_url_list, url_list,cd_path):

    # Define empty lists to store results and log failed URLs
    failed = []
    results = []

    for vatter_url in tqdm(vatter_url_list):

        if vatter_url not in url_list:
            # Empty dictionary to store output
            vatter_results = {}

            # Beautiful soup driver
            HEADERS = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
            }
            content = requests.get(vatter_url, headers=HEADERS)
            soup = BeautifulSoup(content.text, "html.parser")

            # Selenium driver
            user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
            # path = "/Users/ericmestiza/Documents/chromedriver"
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument(f"user-agent={user_agent}")
            driver = webdriver.Chrome(executable_path=cd_path, options=options)
            driver.get(vatter_url)

            try:
                # Product name
                vatter_name = (
                    soup.find("div", {"class": "product-name top-product-detail"})
                    .get_text()
                    .strip("\n")
                    .strip()
                )
                vatter_results["Name"] = vatter_name

                # Product material
                vatter_material = {
                    el.text
                    for el in soup.find("div", {"class": "short-description"})
                    .find("ul")
                    .find_all("li")[4]
                }
                vatter_results["Material"] = vatter_material

                # Product color
                vatter_color = []

                color = (
                    soup.find("div", {"class": "product-name top-product-detail"})
                    .get_text()
                    .strip("\n")
                    .strip()
                )
                color = color.split()
                vatter_color.append(color[-1])

                vatter_results["Color"] = vatter_color

                # Product price
                vatter_price = soup.find("span", {"class": "money"}).get_text().strip()
                vatter_results["Price"] = vatter_price

                # Product URL
                vatter_results["URL"] = vatter_url

                # Product image
                vatter_image = []

                for img in soup.find_all("img", {"class": "img-responsive"}):
                    vatter_image.append("https:" + img["src"])

                vatter_results["Image"] = vatter_image

                # Dictionary of color: image URL
                color_image_dict = {}

                for color in vatter_color:
                    for img in vatter_image:
                        color_image_dict[color] = img

                vatter_results["Color:Image"] = color_image_dict

                # Product description
                vatter_description = [
                    desc.text
                    for desc in driver.find_elements_by_class_name("short-description")
                ]
                vatter_results["Description"] = vatter_description

                # print(vatter_results)

                # Add dictionary output to list
                results.append(vatter_results)

            # TODO: (sarah) I don't think you need the conditional statements here, unless you want to write the kind of error occured ~ do we want to do that?
            except (NoSuchElementException, AttributeError, TypeError):
                if NoSuchElementException:
                    failed.append(vatter_url)
                elif AttributeError:
                    failed.append(vatter_url)
                elif TypeError:
                    failed.append(vatter_url)
                pass

            with open("vatter_table.csv", mode="w") as csv_file:
                writer = csv.DictWriter(
                    csv_file,
                    fieldnames=[
                        "Name",
                        "Material",
                        "Color",
                        "Price",
                        "URL",
                        "Image",
                        "Color:Image",
                        "Description",
                    ],
                )
                writer.writeheader()
                writer.writerows(results)

            with open("failed_vatter.txt", mode="w") as txt_file:
                for row in failed:
                    txt_file.write(str(row) + "\n")


# Scraper
vatter_scraper(vatter_url_list, url_list,cd_path)
