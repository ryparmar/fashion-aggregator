import requests
import json
import urllib.parse
import posixpath
import argparse

from PIL import Image
from io import BytesIO
from typing import Set, List, Dict, Union

from config import HOME_URL

def save_urls_to_file(filepath: str, content: Union[List[str], Set[str]]) -> None:
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
        fw.write(json.dumps(data, ensure_ascii=False) + '\n')

def download_images(img_urls: List[str], filepath: str) -> None:
    """Download images from its urls"""
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