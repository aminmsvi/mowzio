import requests
import logging


def fetch_html(url: str) -> str | None:
    """
    Fetches the HTML content of a given URL, mimicking a browser request.

    Args:
        url: The URL of the website to fetch.

    Returns:
        The HTML content as a string, or None if the request fails.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    }
    logger = logging.getLogger(__name__)
    logger.info(f"Fetching HTML from {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return None
