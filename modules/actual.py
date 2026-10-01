import json
import urllib.error
import urllib.request
from typing import Dict, List, Optional

from .logger import logger

# Without an explicit timeout a hung Actual server parks the sync forever and
# the only way out is the manual stop button.
TIMEOUT_SECONDS = 30


def _post(url: str, body: dict, token: Optional[str] = None, timeout: int = TIMEOUT_SECONDS):
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers=headers,
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # HTTPError carries the status and the response body, which is the only
        # useful thing to log when the import is rejected.
        detail = e.read().decode("utf-8", "replace")[:500]
        logger.error(f"Actual returned HTTP {e.code} for {url}: {detail}")
        raise RuntimeError(f"Actual API returned HTTP {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        logger.error(f"Cannot reach Actual at {url}: {e}")
        raise RuntimeError(f"Cannot reach Actual at {url}: {e}") from e


def init_actual(config: dict) -> str:
    """Open an Actual session and return the bearer token."""
    res = _post(
        f"{config['url']}/api/init",
        {
            "password": config["password"],
            "budgetId": config["budget_id"],
            "budgetPassword": config.get("budget_password"),
        },
    )
    token = (res or {}).get("token")
    if not token:
        raise RuntimeError("Actual /api/init did not return a token")
    return token


def list_accounts(token: str, actual_url: str) -> List[Dict]:
    """Return the budget's accounts so the UI can offer a picker."""
    res = _post(
        f"{actual_url}/api/getAccounts?paramsInBody=true",
        {"_": []},
        token=token,
    )
    return res or []


def import_transactions(
    token: str, account_id: str, transactions: List[Dict], actual_url: str
):
    """Import one account's transactions. Raises on any failure."""
    result = _post(
        f"{actual_url}/api/importTransactions?paramsInBody=true",
        {"_": [account_id, transactions]},
        token=token,
    )
    if result is None:
        raise RuntimeError(f"Actual returned an empty response for account {account_id}")

    errors = result.get("errors") if isinstance(result, dict) else None
    if errors:
        raise RuntimeError(f"Actual rejected transactions for {account_id}: {errors}")

    return result
