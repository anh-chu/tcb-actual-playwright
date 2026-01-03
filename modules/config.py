import os
import json
import logging

logger = logging.getLogger(__name__)

def get_config():
    # Load required environment variables
    tcb_username = os.getenv("TCB_USERNAME")
    tcb_password = os.getenv("TCB_PASSWORD")
    actual_url = os.getenv("ACTUAL_URL")
    actual_password = os.getenv("ACTUAL_PASSWORD")
    actual_budget_id = os.getenv("ACTUAL_BUDGET_ID")
    actual_budget_password = os.getenv("ACTUAL_BUDGET_PASSWORD")
    tcb_accounts_mapping_str = os.getenv("TCB_ACCOUNTS_MAPPING", "{}")

    # Validate critical config
    if not all([tcb_username, tcb_password, actual_url, actual_password, actual_budget_id]):
        logger.warning("Missing one or more required environment variables (TCB_USERNAME, TCB_PASSWORD, ACTUAL_URL, ACTUAL_PASSWORD, ACTUAL_BUDGET_ID). App may not function correctly.")

    # Parse mappings
    # Expected format: {"123456789": "actual_account_uuid", ...}
    try:
        arrangements = json.loads(tcb_accounts_mapping_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse TCB_ACCOUNTS_MAPPING: {e}")
        arrangements = {}

    return (
        arrangements,
        actual_url,
        actual_password,
        actual_budget_id,
        actual_budget_password,
        tcb_username,
        tcb_password,
    )


(
    ARRANGEMENTS,
    ACTUAL_URL,
    ACTUAL_PASSWORD,
    ACTUAL_BUDGET_ID,
    ACTUAL_BUDGET_PASSWORD,
    TCB_USERNAME,
    TCB_PASSWORD,
) = get_config()
