import json


def get_config():
    with open("./uploads/actual_tcb_config.json", "r") as f:
        config = json.load(f)
    arrangements = {
        x: account["id"]
        for account in config["mappings"]
        for x in account.get("arrangementIds", [])
    }
    actual_url = config["actual_url"]
    actual_password = config["actual_password"]
    actual_budget_id = config["actual_budget_id"]
    actual_budget_password = config["actual_budget_password"]
    tcb_username = config["tcb_username"]
    tcb_password = config["tcb_password"]
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
