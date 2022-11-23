import requests
import json
import urllib.parse
import posixpath
import argparse
import logging

from PIL import Image
from io import BytesIO
from typing import Set, List, Dict, Union
from google.cloud import storage

from config import HOME_URL

# Setup module logger
logger = logging.getLogger(__name__)


def get_latest_item_urls_file() -> str:
    """Tries to get the latest file with item urls"""
    pass
    # TODO
    # latest_item_urls_file = ""


def append_urls_to_file(filepath: str, content: Union[List[str], Set[str]]) -> None:
    """Save list or set of urls into a given file. Single url per line."""
    with open(filepath, "a", encoding="utf-8") as fw:
        fw.write("\n".join(content))


def read_urls_from_file(filepath: str) -> List[str]:
    """Read urls from a given file. Single url per line."""
    with open(filepath, "r", encoding="utf-8") as fr:
        return [line.strip() for line in fr.readlines()]


def append_json_to_jsonl_file(output_file: str, data: Dict[str, str]) -> None:
    """Append given data to the file"""
    with open(output_file, "a", encoding="utf-8") as fw:
        fw.write(json.dumps(data, ensure_ascii=False) + "\n")


def download_images(img_urls: List[str], filepath: str) -> None:
    """Download images from list of urls"""
    for i, img_url in enumerate(img_urls):
        # Request the image and open it
        r = requests.get(img_url)
        img = Image.open(BytesIO(r.content))
        # Save image
        img.save(f"{filepath}_{i}.png")


def item_url_to_path(home_url: str, item_url: str) -> str:
    """Converts item url to path like string

    Example:
        In: https://www.vinted.cz/zeny/obleceni/saty/mini-saty/2353299058-deezee-bezove-saty
        Out: zeny/obleceni/saty/mini-saty/2353299058
    """
    return "/".join(item_url.replace(home_url, "").split("/")[:-1])


def construct_starting_urls(args: argparse.Namespace) -> List[str]:
    """Construct the initial pages for scraping"""
    return [urllib.parse.urljoin(HOME_URL, posixpath.join(category, "obleceni")) for category in args.categories]


def remove_duplicate_urls_from_file(filepath: str) -> None:
    urls = read_urls_from_file(filepath)
    unique_urls = set(urls)
    with open(filepath, "w") as fw:
        fw.write("\n".join(unique_urls))
    logger.info(f"Removed duplicates from the file with urls. Before {len(urls)} - after {len(unique_urls)}")


def gcs_upload_file(project_name: str, bucket_name: str, source_file_name: str, destination_file_name: str):
    """Uploads a file to a GCS bucket"""
    storage_client = storage.Client(project_name)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_file_name)
    blob.upload_from_filename(source_file_name)
    logger.info(f"File {source_file_name} uploaded to {destination_file_name}.")


def gcs_upload_file_from_variale(project_name: str, bucket_name: str, source_variable: str, destination_file_name: str):
    """Uploads variable to file to a GCS bucket"""
    storage_client = storage.Client(project_name)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_file_name)
    blob.upload_from_string(source_variable)
    logger.info(f"{destination_file_name} uploaded to {bucket_name}.")
