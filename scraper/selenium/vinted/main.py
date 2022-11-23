import os
import datetime
import logging
import pathlib
import chromedriver_binary  # Adds chromedriver binary to path

from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from google.cloud import storage

from scraper.scrape_item_urls import scrape_item_urls
from scraper.scraping import click_to_reject_all_cookies_button
from scraper.utils import remove_duplicate_urls_from_file, gcs_upload_file
from scraper.config import HOME_URL, SITE_NAME, GCP_PROJECT, GCS_STORAGE

app = Flask(__name__)

# The following options are required to make headless Chrome work in a Docker container
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("window-size=1024,768")
chrome_options.add_argument("--no-sandbox")

# Setup driver
service = Service()
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.implicitly_wait(5)

# Go to home url and reject all cookies
driver.get(HOME_URL)
click_to_reject_all_cookies_button(driver)

logger = logging.getLogger(__name__)


@app.route("/")
def index():
    return "Application is running"

@app.route("/arguments/<categories>/<debug>")
def arguments(categories, debug):
    return f"Arguments:\n\tcategories: {categories}\n\tdebug: {debug}"

@app.route("/scrape-urls")
def scrape_item_urls():
    args = {
        "categories": ["zeny", "muzi"],
        "max_pages": 3,
        "output_dir": "data",
        "output_file": f"item_urls_{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')}.txt",
        "save_to_gcs": True,
        "clean_local_data": True,
        "debug": True
    }

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

    scrape_item_urls(args, driver)

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
        os.remove(log_filepath)
        for category in args.categories:
            url_filepath = os.path.join(args.output_dir, "item_urls", SITE_NAME, category, args.output_file)
            os.remove(url_filepath)
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"{SITE_NAME} item_urls for {args.categories} categories were scraped. Start time {start_time} - end time {end_time}"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))