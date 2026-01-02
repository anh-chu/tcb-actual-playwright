import urllib.request
import json

from .config import (
    ACTUAL_URL,
    ACTUAL_PASSWORD,
    ACTUAL_BUDGET_ID,
    ACTUAL_BUDGET_PASSWORD,
)


def init_actual():
    url = f"{ACTUAL_URL}/api/init"

    # Prepare the request body
    body = {
        "password": ACTUAL_PASSWORD,
        "budgetId": ACTUAL_BUDGET_ID,
        "budgetPassword": ACTUAL_BUDGET_PASSWORD,
    }

    # Convert body to JSON string
    body_json = json.dumps(body).encode("utf-8")

    # Create request object
    req = urllib.request.Request(
        url,
        data=body_json,
        method="POST",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )

    # Send the request and read the response
    try:
        with urllib.request.urlopen(req) as response:
            # Read and decode the response
            response_body = response.read().decode("utf-8")

            # Parse the JSON response
            res = json.loads(response_body)

            # Return the token
            return res["token"]



    except urllib.error.URLError as e:
        # Handle any network-related errors
        from .logger import logger
        logger.error(f"Error occurred: {e}")
        return None


def import_transactions(token, account_id, transactions):
    url = f"{ACTUAL_URL}/api/importTransactions?paramsInBody=true"

    # Prepare the request body
    body = {"_": [account_id, transactions]}

    # Convert body to JSON string
    body_json = json.dumps(body).encode("utf-8")

    # Create request object
    req = urllib.request.Request(
        url,
        data=body_json,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )

    # Send the request and read the response
    try:
        with urllib.request.urlopen(req) as response:
            # Read and decode the response
            response_body = response.read().decode("utf-8")

            # Parse the JSON response
            return json.loads(response_body)

    except urllib.error.URLError as e:
        # Handle any network-related errors

        from .logger import logger
        logger.error(f"Error occurred: {e}")
        return None
