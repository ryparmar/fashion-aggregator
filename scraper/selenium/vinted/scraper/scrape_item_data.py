import argparse
import logging
import datetime
import time
import os
import pathlib
import glob
import shutil

from random import randint
from typing import Union, Dict, Any
from selenium import webdriver

from config import HOME_URL, SITE_NAME, GCP_PROJECT, GCS_STORAGE
from scraping import setup_driver, scrape_element, scrape_elements, scrape_image_urls
from utils import download_images, item_url_to_path, read_urls_from_file, append_json_to_jsonl_file, gcs_upload_file


def scrape_item(args: Union[Dict[str, Any], argparse.Namespace], driver: webdriver, item_url: str) -> Dict[str, str]:
    """Function saves scraped data to a jsonl file and then saves also images for given item"""
    # Go to item page
    driver.get(item_url)

    # Scrape data
    time.sleep(randint(3, 5))
    item_data = {
        "id": item_url.rstrip("/").split("/")[-1].split("-")[0],
        "url": item_url,
        "price": scrape_element(driver, "div[id^=ItemPriceHeading]"),
        "description": scrape_element(driver, "div[itemprop=name]")
        + "\n\n"
        + scrape_element(driver, "div[itemprop=description]").replace("\n\nNakup pres tlacitko ANO", ""),
    }
    # item_data["price"] = scrape_element(driver, "div[id^=ItemPriceHeading]")
    # item_data["description"] = scrape_element(driver, "div[itemprop=name]") + "\n" + scrape_element(driver, "div[itemprop=description]")

    titles = scrape_elements(driver, "div[class=details-list__item-title]")
    values = scrape_elements(driver, "div[class=details-list__item-value]")
    for title, value in zip(titles[:4], values[:4]):
        item_data[title] = value.split("\n")[0]

    # Scrape image urls
    img_urls = scrape_image_urls(driver, "figure[class^=item-description] a")
    # Create directories if not exists
    img_output_filename = os.path.join(
        args.output_dir, "item_data", SITE_NAME, "images", item_url_to_path(HOME_URL, item_url), item_data["id"]
    )
    img_output_filename_parent = pathlib.Path(img_output_filename).parent
    img_output_filename_parent.mkdir(parents=True, exist_ok=True)

    # Create directories if not exists
    data_output_filename = os.path.join(args.output_dir, "item_data", SITE_NAME, "data", args.output_file)
    data_output_filename_parent = pathlib.Path(img_output_filename).parent
    data_output_filename_parent.mkdir(parents=True, exist_ok=True)

    # Save json data
    item_data["img_path"] = img_output_filename
    item_data["num_of_images"] = len(img_urls)
    if args.debug:
        logging.info(f"Scraped data for {item_data} saved to file")
    else:
        logging.info(f"Scraped data for {item_data['id']} saved to file")
    append_json_to_jsonl_file(data_output_filename, item_data)

    # Download images
    download_images(img_urls, img_output_filename)
    logging.info(f"Found {len(img_urls)} images. Saved in {img_output_filename}")


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Process given arguments")
    parser.add_argument(
        "--item-urls-file",
        dest="item_urls_file",
        required=True,
        type=str,
        help="Input file with item urls. Expected format is a single url per line.",
    )
    parser.add_argument(
        "--max-items",
        dest="max_items",
        default=None,
        required=False,
        type=int,
        help="Max number of items to be scraped. Set some low number for debugging.",
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
        default=f"item_data_{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')}.jsonl",
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
        default=False,
        help="If debug True, than only a part of the website is scraped.",
    )
    args = parser.parse_args()

    # Check arguments
    if args.debug:
        vars(args)["max_items"] = 3
    # TODO
    # if args.item_urls_file in set("latest", "last"):
    #     vars(args)["item_urls_file"] = get_latest_item_urls_files()
    if not os.path.exists(args.item_urls_file):
        raise ValueError(f"Non-existing file with urls {args.item_urls_file}")

    # Setup logger
    log_filepath = f"logs/{SITE_NAME}/{args.output_file.replace('.jsonl', '.log')}"
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
    logging.info(f"Started at {start_time}")
    if args.debug:
        logging.info("Running in a debug mode")
    args_str = "\n".join(["\t{}: {}".format(k, v) for k, v in vars(args).items()])
    logging.info(f"Given arguments:\n{args_str}")

    try:
        driver = setup_driver()
        # Scrape item data
        item_urls = read_urls_from_file(args.item_urls_file)[: args.max_items]
        num_of_urls = len(item_urls)
        for i, item_url in enumerate(item_urls):
            logging.info(f"Scraping item {i+1}/{num_of_urls} from {item_url}")
            scrape_item(args, driver, item_url)
            time.sleep(randint(3, 5))
    finally:
        # Close webdriver
        driver.close()
        driver.quit()

    # Save data to GCS
    if args.save_to_gcs:
        gcs_upload_file(GCP_PROJECT, GCS_STORAGE, log_filepath, log_filepath)  # save log
        filepaths = glob.glob(
            f'{os.path.join(args.output_dir, "item_data", SITE_NAME, "images")}/**/*.png', recursive=True
        )
        for filepath in filepaths:
            gcs_upload_file(GCP_PROJECT, GCS_STORAGE, filepath, filepath)

    # Remove local data
    if args.clean_local_data:
        shutil.rmtree("logs")
        shutil.rmtree(args.output_dir)


if __name__ == "__main__":
    main()
