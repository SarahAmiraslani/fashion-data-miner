"""
This module contains utility functions for web scraping.

It includes functions to generate a random user agent for making requests, and to prepare a Selenium WebDriver with specific options.

The user agent string is randomly selected from a list of user agents for Chrome running on Windows, Mac, or Linux.

This module uses several third-party libraries:
- extruct for extracting structured data from webpages.
- requests for making HTTP requests.
- Selenium for automating web browser interactions.
- w3lib for handling URLs and web page encodings.
- random_user_agent for generating random user agent strings.

This module is intended to be used as a utility module for the larger web scraping project.
"""

# Standard library imports
from urllib.request import Request, urlopen

# Related third party imports
import extruct
from extruct.microformat import MicroformatExtractor
import requests
from selenium import webdriver
from w3lib.html import get_base_url
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem


# ---- web scrapping ----


def get_user_agent() -> str:
    """
    Defines a random user agent string for web scraping purposes.

    Returns:
        str: A randomly selected user agent string.
    """

    software_names = [SoftwareName.CHROME.value]
    operating_systems = [
        OperatingSystem.WINDOWS.value,
        OperatingSystem.MAC.value,
        OperatingSystem.LINUX.value,
    ]
    user_agent_rotator = UserAgent(
        software_names=software_names, operating_systems=operating_systems, limit=100
    )
    return user_agent_rotator.get_random_user_agent()


def get_metadata(url: str, metadata_type: str = "all-in-one") -> dict:
    """
    Retrieves the metadata from the specified URL.

    Args:
        url (str): The URL of the webpage.
        metadata_type (str): The type of metadata to extract. Supported values are "all-in-one" and "micro".

    Returns:
        dict: The extracted metadata.

    Raises:
        ValueError: If an unsupported metadata_type is provided.
        requests.exceptions.RequestException: If there is an error while making the network request.
    """
    if metadata_type not in ["all-in-one", "micro"]:
        raise ValueError(f"Unsupported metadata_type: {metadata_type}")

    user_agent = get_user_agent()

    try:
        r = requests.get(url, headers={"User-Agent": user_agent}, timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"Error while making network request: {e}")
        raise

    base_url = get_base_url(r.text, r.url)
    data_extractors = {
        "all-in-one": lambda: extruct.extract(r.text, base_url=base_url),
        "micro": lambda: MicroformatExtractor().extract(r.text),
    }

    return data_extractors[metadata_type]()


def get_sitemap(url: str, user_agent: str) -> str:
    """
    Retrieves the sitemap content from the specified URL.

    Args:
        url (str): The URL of the sitemap.
        user_agent (str): The user agent to be used for the request.

    Returns:
        str: The content of the sitemap as a string.

    Raises:
        urllib.error.HTTPError: If there is an HTTP error while retrieving the sitemap.
        urllib.error.URLError: If there is a URL error while retrieving the sitemap.
        UnicodeDecodeError: If there is an error decoding the sitemap content.
    """
    req = Request(url, headers={"User-Agent": user_agent})
    return urlopen(req).read().decode("utf-8")


def prep_driver(user_agent: str) -> webdriver.ChromeOptions:
    """
    Prepares and returns a ChromeOptions object with the specified user agent.

    Args:
        user_agent (str): The user agent string to be used by the Chrome driver.

    Returns:
        webdriver.ChromeOptions: A ChromeOptions object with the specified user agent and other default options.
    """
    options = webdriver.ChromeOptions()
    arguments = [
        "--headless",
        "--no-sandbox",
        "--incognito",
        "--start-maximized",
        "--enable-automation",
        "--ignore-certificate-errors",
        "--disable-notifications",
        "--disable-extensions",
        "--disable-infobars",
        f"user-agent={user_agent}",
    ]

    for argument in arguments:
        options.add_argument(argument)

    return options
