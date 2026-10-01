import json
from pprint import pprint
from typing import Dict, List

from fastnumbers import try_real
from itertools import groupby
from operator import itemgetter

from .exchange_rate import get_exchange_rate


def convert_transaction(transaction: Dict, mapping: Dict):
    """Map one TCB transaction to an Actual Budget transaction.

    Amounts are converted to minor units (VND dong -> cents, x100) because that
    is what Actual's import API expects. imported_id carries the TCB transaction
    id so Actual deduplicates re-runs.
    """
    if not mapping:
        return None

    # mapping is {arrangementId: actualAccountId}
    account_id = mapping.get(transaction["arrangementId"])

    if not account_id:
        return

    amount = try_real(transaction["transactionAmountCurrency"]["amount"])
    currency = transaction["transactionAmountCurrency"]["currencyCode"]

    out = {
        "imported_id": transaction["id"],
        "date": transaction["bookingDate"],
        "amount": round(amount * 100),
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


def active_arrangements(transactions: List[Dict]) -> Dict[str, int]:
    """Count fetched transactions per arrangementId.

    This is the census the routing checks are built on: which bank arrangements
    actually had activity in the window, and how much.
    """
    counts: Dict[str, int] = {}
    for t in transactions:
        arrangement = t.get("arrangementId")
        if arrangement:
            counts[arrangement] = counts.get(arrangement, 0) + 1
    return counts


def unmapped_arrangements(transactions: List[Dict], mapping: Dict) -> Dict[str, int]:
    """Count transactions whose arrangementId is missing from the mapping.

    convert_transaction() silently drops these, so without this the only symptom
    of a new card or account is transactions quietly not appearing in the budget.
    """
    return {
        arrangement: count
        for arrangement, count in active_arrangements(transactions).items()
        if arrangement not in mapping
    }


def invalid_targets(
    transactions: List[Dict], mapping: Dict, known_account_ids
) -> Dict[str, Dict]:
    """Arrangements mapped to an Actual account that does not exist.

    Actual's import accepts an unknown account id and files the rows under it,
    where nothing can ever display them: the sync reports success and the
    transactions silently vanish. These arrangements must not be imported.
    """
    known = set(known_account_ids)
    return {
        arrangement: {"account": mapping[arrangement], "transactions": count}
        for arrangement, count in active_arrangements(transactions).items()
        if arrangement in mapping and mapping[arrangement] not in known
    }


def convert_to_transactions(transactions: List[Dict], mapping: Dict):
    converted = list(
        filter(lambda x: x, [convert_transaction(t, mapping) for t in transactions])
    )
    if not converted:
        return {}

    converted = sorted(converted, key=itemgetter("account"))

    return {
        key: list(group) for key, group in groupby(converted, key=itemgetter("account"))
    }


if __name__ == "__main__":
    with open("../data.json", "r") as f:
        data = json.load(f)
        transactions = convert_to_transactions(data, {})
        pprint(transactions)
