import datetime
import json
import urllib.error
import urllib.request
from typing import Dict, Optional

from .logger import logger

# Kept on @latest on purpose: the rate has to be current, so pinning a
# date-versioned release would freeze the rate at whatever day it was pinned.
BASE_URL = (
    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/"
)

TIMEOUT_SECONDS = 10

# get_exchange_rate is called once per transaction by the converter, so without
# a cache a batch of N foreign-currency transactions issues N HTTP requests.
# Cache is keyed by currency and dropped when the calendar day changes.
_cache: Dict[str, float] = {}
_cache_day: Optional[str] = None


def _reset_if_new_day(day: str) -> None:
    global _cache_day
    if _cache_day != day:
        _cache.clear()
        _cache_day = day


def get_exchange_rate(currency: str) -> float:
    day = datetime.date.today().isoformat()
    _reset_if_new_day(day)

    key = currency.lower()
    if key in _cache:
        return _cache[key]

    url = BASE_URL + key + ".min.json"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            j = json.loads(response.read())
        rate = float(j[key]["vnd"])
    except urllib.error.URLError as e:
        logger.error(f"Failed to fetch exchange rate for {currency}: {e}")
        raise RuntimeError(f"Cannot get exchange rate for {currency}: {e}") from e
    except (KeyError, TypeError, ValueError) as e:
        logger.error(f"Unexpected exchange rate response for {currency}: {e}")
        raise RuntimeError(f"Malformed exchange rate data for {currency}") from e

    _cache[key] = rate
    return rate
