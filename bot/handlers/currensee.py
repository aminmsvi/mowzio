import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ContextTypes

from app.config import settings
from app.db.redis import RedisFactory, RedisAdapter
from bot.decorators import authorized
from utils import fetch_html


# Define a structure for the items to scrape
@dataclass
class ExchangeRateItem:
    icon: str
    name: str
    price: Optional[int] = None


logger = logging.getLogger(__name__)

CACHE_KEY = "exchange_rates"
CACHE_TTL = 3 * 60 * 60  # 3 hours

# Configuration for items to scrape (tag, id, icon, name)
ITEMS_TO_SCRAPE: List[Tuple[str, str, str, str]] = [
    ("td", "usd1", "🇺🇸", "USD"),
    ("td", "eur1", "🇪🇺", "EUR"),
    ("td", "azadi1", "🪙", "Azadi"),
    ("td", "emami1", "🪙", "Emami"),
    ("td", "azadi1_2", "🪙", "Half Azadi"),
    ("td", "azadi1_4", "🪙", "Quarter Azadi"),
    ("span", "gol18", "✨", "Gold 18"),
]

# Default error messages
ERROR_FETCH_FAILED = "Looks like the market hamsters are on a coffee break. Couldn't fetch the rates just now!"
ERROR_CACHE = "The cache seems to be playing hide-and-seek. Couldn't retrieve rates due to cache shenanigans."
ERROR_UNEXPECTED = "Uh oh! Something went sideways in the matrix while fetching rates. Maybe try again?"


@authorized
async def currensee(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """
    Handler for the /exchange_rates command. Fetches exchange rates, using cache if possible.
    """
    redis_adapter = RedisFactory.create_redis_adapter()
    response_message = ERROR_FETCH_FAILED  # Default message

    try:
        # Try fetching from cache first
        cached_rates_json = redis_adapter.get(CACHE_KEY)
        if cached_rates_json:
            logger.info("Cache hit for exchange rates.")
            rates_data = json.loads(cached_rates_json)
            # Convert list of dicts back to list of ExchangeRateItem objects
            rates = [ExchangeRateItem(**item) for item in rates_data]
        else:
            logger.info("Cache miss for exchange rates. Fetching fresh data.")
            rates = await _fetch_and_cache_rates(redis_adapter)

        # Format the response message if rates were successfully obtained
        if rates:
            response_message = _format_rates_in_markdown_v2(rates)
        # else: Keep the default ERROR_FETCH_FAILED message

    except redis_adapter.RedisAdapterError as e:
        logger.error(f"Redis error during exchange rate retrieval: {e}")
        response_message = ERROR_CACHE
    except Exception as e:
        logger.exception(f"An unexpected error occurred in exchange_rates handler: {e}")
        response_message = ERROR_UNEXPECTED

    if update.message:
        await update.message.reply_html(response_message)
    else:
        logger.warning("Update message was None in exchange_rates handler.")


def _format_rates_in_markdown_v2(rates):
    response_lines = ["<b>Exchange Rates:</b>\n"]
    for item in rates:
        if item.price is not None:
            formatted_price = f"{item.price:,}"  # Add thousands separator
            response_lines.append(
                f"{item.icon} <b>{item.name}</b>: <code>{formatted_price}</code>"
            )
        else:
            response_lines.append(f"{item.icon} <b>{item.name}</b>: Not Available")
    return "\n".join(response_lines)


async def _fetch_and_cache_rates(redis_adapter: RedisAdapter) -> List[ExchangeRateItem]:
    """Fetches fresh rates, caches them, and returns them."""
    rates = _fetch_fresh_exchange_rates()
    if rates:
        try:
            # Convert list of dataclasses to list of dicts for JSON serialization
            rates_data = [asdict(item) for item in rates]
            rates_json = json.dumps(rates_data)
            redis_adapter.set(CACHE_KEY, rates_json, expiry=CACHE_TTL)
            logger.info(f"Cached fresh exchange rates for {CACHE_TTL} seconds.")
        except redis_adapter.RedisAdapterError as e:
            # Log cache write error but proceed with the fetched rates
            logger.error(f"Failed to cache fresh exchange rates: {e}")
        except TypeError as e:
            # Log serialization error but proceed with the fetched rates
            logger.error(f"Failed to serialize exchange rates for caching: {e}")
    else:
        logger.error("Failed to fetch fresh exchange rates.")
    return rates


def _fetch_fresh_exchange_rates() -> List[ExchangeRateItem]:
    """Fetches and parses fresh exchange rate data from the source URL."""
    logger.info(f"Attempting to fetch HTML from {settings.BONBAST_URL}")
    html_content = fetch_html(settings.BONBAST_URL)
    if not html_content:
        logger.error(f"Failed to fetch HTML content from {settings.BONBAST_URL}.")
        return []

    try:
        soup = BeautifulSoup(html_content, "html.parser")
        extracted_rates: List[ExchangeRateItem] = []

        for tag, price_id, icon, name in ITEMS_TO_SCRAPE:
            price = _extract_price_by_id(tag, price_id, soup)
            extracted_rates.append(ExchangeRateItem(icon=icon, name=name, price=price))

        # Log if any prices could not be extracted
        failed_items = [item.name for item in extracted_rates if item.price is None]
        if failed_items:
            logger.warning(f"Could not extract prices for: {', '.join(failed_items)}")

        return extracted_rates

    except Exception as e:  # Catch potential errors during parsing
        logger.exception(
            f"An unexpected error occurred during HTML parsing or price extraction: {e}"
        )
        return []


def _extract_price_by_id(tag: str, price_id: str, soup: BeautifulSoup) -> Optional[int]:
    """Extracts price text by tag and ID, cleans it, and converts to int."""
    price_tag = soup.find(name=tag, id=price_id)
    if not price_tag:
        logger.error(f"Price tag with tag='{tag}' and id='{price_id}' not found.")
        return None

    price_text = price_tag.text.strip().replace(",", "")
    if not price_text:
        logger.warning(f"Price tag with id='{price_id}' has empty text.")
        return None

    try:
        return int(price_text)
    except ValueError:
        logger.error(
            f"Error converting price text '{price_text}' to int for id='{price_id}'."
        )
        return None


# --- Test Script ---
if __name__ == "__main__":
    # Create some sample data for testing
    sample_rates = [
        ExchangeRateItem(icon="🇺🇸", name="USD", price=81000),
        ExchangeRateItem(icon="🇪🇺", name="EUR", price=92350),
        ExchangeRateItem(icon="🪙", name="Azadi", price=68400000),
        ExchangeRateItem(
            icon="❓", name="Unknown", price=None
        ),  # Test case with None price
    ]

    # Call the function and print the result
    formatted_output = _format_rates_in_markdown_v2(sample_rates)
    print("--- Testing _format_rates ---")
    print(formatted_output)
    print("--- End Test ---")
