import argparse
import logging
import datetime
import time
import os

from random import randint
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from config import BINARY_PATH, DRIVER_PATH, CATEGORY_CHOICES
from utils import construct_starting_urls, save_urls_to_file
from scraping import click_to_reject_all_cookies_button, get_next_page_button, get_item_urls_from_page


def scrape_item_urls(args, driver) -> None:
    """Function that scrapes all the pages"""
    starting_urls = construct_starting_urls(args)
    logging.info(f"Starting urls {starting_urls}")
    for starting_url in starting_urls:
        logging.info(f"Scraping {starting_url}")
        driver.get(starting_url)
        click_to_reject_all_cookies_button(driver)

        return_urls = set()
        current_page = 1
        max_pages = args.max_pages if hasattr(args, "max_pages") and args.max_pages else float("inf")
        next_page_button = get_next_page_button(driver)
        while next_page_button and current_page <= max_pages:
            # Scrape item urls
            logging.info(f"Scraping page {current_page} of {starting_url}")
            page_urls = get_item_urls_from_page(driver)
            logging.info(f"Scraped {len(page_urls)} urls for page {current_page}")
            return_urls = return_urls.union(page_urls)
            time.sleep(randint(3, 5))

            # Save into file
            save_urls_to_file(
                os.path.join(os.path.join(args.output_dir, f"{args.category}_{args.output_file}")), return_urls
            )
            logging.info(f"Saving into file")

            # Go to next page if available
            next_page_button = get_next_page_button(driver)
            if not next_page_button:
                logging.info(f"There are no more pages. Current page is {current_page}.")
                break
            next_page_button.click()
            current_page += 1
            time.sleep(randint(3, 5))

        logging.info(
            f"Scraping for {starting_url} finished.",
            f"Found {len(return_urls)} items that were saved into {args.output_file}",
        )


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Process given arguments")
    parser.add_argument(
        "categories", metavar="N", type=str, nargs="+", choices=CATEGORY_CHOICES, help="Categories to be scraped."
    )
    parser.add_argument(
        "--max-pages",
        dest="max_pages",
        required=False,
        type=int,
        help="Max number of pages to be scraped. Set some low number for debugging.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        dest="output_dir",
        type=str,
        default="data",
        help="Output directory where all the scraped data will be saved.",
    )
    parser.add_argument(
        "-f",
        "--output-file",
        dest="output_file",
        type=str,
        default=f"vinted_item_urls_{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')}.txt",
        help="Output file where all the scraped data will be saved.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="If debug True, than only a part of the website is scraped.",
    )
    args = parser.parse_args()
    if args.debug:
        vars(args)["max_pages"] = 3

    # Setup logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(f"logs/{'.'.join(args.output_file.split('.')[:-1])}.log"),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger()
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Started at {start_time}")
    args_str = "\n".join(["\t{}: {}".format(k, v) for k, v in vars(args).items()])
    logger.info(f"Given arguments:\n{args_str}")

    # Setup webdriver
    options = webdriver.ChromeOptions()
    options.binary_location = BINARY_PATH
    service = Service(DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)

    # Scraper item urls
    scrape_item_urls(args, driver)

    # Close webdriver
    driver.close()
    driver.quit()


if __name__ == "__main__":
    main()
