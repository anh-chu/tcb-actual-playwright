import json
from pprint import pprint
from typing import List, Dict
from fastnumbers import try_real
from itertools import groupby
from operator import itemgetter
from functools import reduce

from .exchange_rate import get_exchange_rate



def convert_to_actual_transaction(transaction: Dict, mapping: Dict):
    if not mapping:
        return None

    # Find account ID from arrangement ID
    # mapping is {arrangementId: accountId}
    account_id = mapping.get(transaction["arrangementId"])

    if not account_id:
        return

    amount = try_real(transaction["transactionAmountCurrency"]["amount"])
    currency = transaction["transactionAmountCurrency"]["currencyCode"]

    out = {
        "imported_id": transaction["id"],
        "date": transaction["bookingDate"],
        "amount": int(amount) * 100,
        "payee_name": transaction.get("counterPartyName"),
        "notes": transaction["description"].removeprefix(
            "Giao dich thanh toan/Purchase - So The/Card No:"
        ),
        "account": account_id,
    }

    if currency != "VND":
        exchange_rate = get_exchange_rate(currency)
        out["amount"] = round(amount * exchange_rate * 100)

    out["amount"] = (
        -out["amount"]
        if transaction["creditDebitIndicator"] == "DBIT"
        else out["amount"]
    )

    if "counterPartyAccountNumber" in transaction:
        out["notes"] += f" @ {transaction['counterPartyAccountNumber']}"

    return out


def convert_to_actual_import(transactions: List[Dict], mapping: Dict):
    # Pass mapping to inner function
    a = list(filter(lambda x: x, [convert_to_actual_transaction(t, mapping) for t in transactions]))
    if not a:
        return {}
        
    a = sorted(a, key=itemgetter("account"))

    converted = {
        key: list(group) for key, group in groupby(a, key=itemgetter("account"))
    }

    return converted


if __name__ == "__main__":
    with open("../data.json", "r") as f:
        data = json.load(f)
        transactions = convert_to_actual_import(data)
        pprint(transactions)
