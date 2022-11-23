import argparse
import logging
import datetime
import pathlib
import time
import os
import shutil

from random import randint
from selenium import webdriver
from typing import Union, Dict, Any

from config import CATEGORY_CHOICES, GCP_PROJECT, GCS_STORAGE, SITE_NAME
from utils import construct_starting_urls, append_urls_to_file, remove_duplicate_urls_from_file, gcs_upload_file
from scraping import setup_driver, get_next_page_button, get_item_urls_from_page

# Setup module logger
# https://stackoverflow.com/questions/22231809/is-it-better-to-use-root-logger-or-named-logger-in-python
logger = logging.getLogger(__name__)


def scrape_item_urls(args: Union[Dict[str, Any], argparse.Namespace], driver: webdriver) -> None:
    """Function that scrapes all the pages"""
    max_pages = args.max_pages if hasattr(args, "max_pages") and args.max_pages else 1000  # TODO float("inf")
    starting_urls = construct_starting_urls(args)
    logger.info(f"Starting urls {starting_urls}")
    for category, starting_url in zip(args.categories, starting_urls):
        logger.info(f"Scraping {category} starting with {starting_url}")
        # Prepare filepath and directories if not exist
        output_filepath = os.path.join(args.output_dir, "item_urls", SITE_NAME, category, args.output_file)
        output_filepath_parent = pathlib.Path(output_filepath).parent
        output_filepath_parent.mkdir(parents=True, exist_ok=True)

        driver.get(starting_url)

        current_page = 1
        next_page_button = get_next_page_button(driver)
        while next_page_button and current_page <= max_pages:
            # Scrape item urls
            logger.info(f"Scraping page {current_page} of {category}")
            page_urls = set(get_item_urls_from_page(driver))
            logger.info(f"Scraped {len(page_urls)} urls for page {current_page}")
            time.sleep(randint(3, 5))

            # Save into file
            append_urls_to_file(output_filepath, page_urls)
            logger.info(f"Saved into file")

            # Go to next page if available
            next_page_button = get_next_page_button(driver)
            if not next_page_button:
                logger.info(f"There are no more pages. Current page is {current_page}.")
                break
            next_page_button.click()
            current_page += 1
            time.sleep(randint(3, 5))

        logger.info(
            f"Scraping for {starting_url} finished at page {current_page}. Items were saved into {output_filepath}",
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
        "-d",
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
        default=f"item_urls_{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')}.txt",
        help="Output file where all the scraped data will be saved.",
    )
    parser.add_argument(
        "--save-to-gcs",
        action="store_true",
        dest="save_to_gcs",
        default=False,
        help="If True, then scraped data are saved on GCS.",
    )
    parser.add_argument(
        "--clean-local-data",
        action="store_true",
        dest="clean_local_data",
        default=False,
        help="If True, then local data - logs and scraped data will be removed at the end",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        dest="debug",
        default=False,
        help="If True, then only a tiny part of the website is scraped.",
    )
    args = parser.parse_args()

    # Check arguments
    if args.debug:
        vars(args)["max_pages"] = 3
    assert args.output_file.endswith(".txt"), f"Unexpected suffix of output file. Make sure you use .txt suffix."

    # Setup logger
    log_filepath = f"logs/{SITE_NAME}/{args.output_file.replace('.txt', '.log')}"
    pathlib.Path(f"logs/{SITE_NAME}").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_filepath),
            logging.StreamHandler(),
        ],
    )
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Started at {start_time}")
    if args.debug:
        logging.info("Running in a debug mode")
    args_str = "\n".join(["\t{}: {}".format(k, v) for k, v in vars(args).items()])
    logging.info(f"Given arguments:\n{args_str}")

    try:
        driver = setup_driver()
        scrape_item_urls(args, driver)
    finally:
        # Close webdriver
        driver.close()
        driver.quit()

    # Deduplicate the urls
    for category in args.categories:
        url_filepath = os.path.join(args.output_dir, "item_urls", SITE_NAME, category, args.output_file)
        remove_duplicate_urls_from_file(url_filepath)

    # Save data to GCS
    if args.save_to_gcs:
        gcs_upload_file(GCP_PROJECT, GCS_STORAGE, log_filepath, log_filepath)  # save log
        for category in args.categories:
            url_filepath = os.path.join(args.output_dir, "item_urls", SITE_NAME, category, args.output_file)
            gcs_upload_file(GCP_PROJECT, GCS_STORAGE, url_filepath, url_filepath)

    # Remove local data
    if args.clean_local_data:
        shutil.rmtree("logs")
        shutil.rmtree(args.output_dir)


if __name__ == "__main__":
    main()
