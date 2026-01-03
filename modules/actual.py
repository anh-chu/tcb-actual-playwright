import urllib.request
import json




def init_actual(config: dict):
    url = f"{config['url']}/api/init"

    # Prepare the request body
    body = {
        "password": config['password'],
        "budgetId": config['budget_id'],
        "budgetPassword": config.get('budget_password'),
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


def import_transactions(token, account_id, transactions, actual_url):
    url = f"{actual_url}/api/importTransactions?paramsInBody=true"

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
