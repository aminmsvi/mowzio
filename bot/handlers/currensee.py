import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any

import requests
from requests.exceptions import RequestException, Timeout, JSONDecodeError
from telegram import Update
from telegram.ext import ContextTypes
from app.config import settings
from app.db.redis import RedisFactory, RedisAdapter
from bot.decorators import authorized


# Define a structure for the items to scrape
@dataclass
class ExchangeRateItem:
    icon: str
    name: str
    price: Optional[int] = None


@dataclass
class NavasanResponse:
    """Schema for the Navasan API response"""

    data: Dict[str, Dict[str, str]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NavasanResponse":
        return cls(data=data)


logger = logging.getLogger(__name__)

CACHE_KEY = "exchange_rates"
CACHE_TTL = 2 * 60 * 60
REQUEST_TIMEOUT_SECONDS = 10

# Configuration for items to scrape (key, icon, name)
ITEMS: List[Tuple[str, str, str]] = [
    ("usd", "🇺🇸", "USD"),
    ("eur", "🇪🇺", "EUR"),
    ("sekkeh", "🪙", "Emami"),
    ("bahar", "🪙", "Azadi"),
    ("nim", "🪙", "Half Azadi"),
    ("rob", "🪙", "Quarter Azadi"),
    ("18ayar", "✨", "Gold 18"),
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


def _format_rates_in_markdown_v2(rates: List[ExchangeRateItem]) -> str:
    """Format exchange rates for HTML display in Telegram."""
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
    rates = await _fetch_fresh_exchange_rates()
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


async def _fetch_fresh_exchange_rates() -> List[ExchangeRateItem]:
    """Fetches and parses fresh exchange rate data from the source URL."""
    api_url = f"http://api.navasan.tech/latest/?api_key={settings.NAVASAN_API_KEY}"
    logger.info(f"Attempting to fetch data from Navasan API")

    session = requests.Session()
    extracted_rates: List[ExchangeRateItem] = []

    try:
        response = session.get(api_url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        data = response.json()
        if not data:
            logger.error("Empty response from Navasan API")
            return []

        api_response = NavasanResponse.from_dict(data)

        for key, icon, name in ITEMS:
            price_str = api_response.data.get(key, {}).get("value")
            price = int(price_str) if price_str else None
            extracted_rates.append(ExchangeRateItem(icon=icon, name=name, price=price))

        # Log if any prices could not be extracted
        failed_items = [item.name for item in extracted_rates if item.price is None]
        if failed_items:
            logger.warning(f"Could not extract prices for: {', '.join(failed_items)}")

    except Timeout:
        logger.error(
            f"Request to Navasan API timed out after {REQUEST_TIMEOUT_SECONDS} seconds"
        )
    except JSONDecodeError:
        logger.error("Failed to parse JSON response from Navasan API")
    except RequestException as e:
        logger.error(f"Request error while fetching from Navasan API: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error processing exchange rates: {e}")
    finally:
        session.close()

    return extracted_rates
