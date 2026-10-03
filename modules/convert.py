import json
import re
from pprint import pprint
from typing import Dict, List

from fastnumbers import try_real
from itertools import groupby
from operator import itemgetter

from .exchange_rate import get_exchange_rate

# For foreign-currency card purchases TCB writes the amount it actually settled in VND
# into the description, e.g. "... Twitch Interactive, Inc. So tien sau khi quy doi: 205958 VND".
_SETTLED_VND = re.compile(r"quy doi:\s*(\d+)\s*VND", re.IGNORECASE)


def settled_vnd(description):
    """Return the VND amount the bank settled for a foreign-currency row, or None."""
    m = _SETTLED_VND.search(description or "")
    return int(m.group(1)) if m else None


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
        # Prefer the bank's own settled VND; fall back to our rate lookup when the
        # description does not carry one (e.g. refunds/reverts).
        settled = settled_vnd(transaction.get("description"))
        if settled is not None:
            out["amount"] = settled * 100
        else:
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


def unmapped_arrangements(transactions: List[Dict], mapping: Dict) -> Dict[str, int]:
    """Count transactions whose arrangementId is missing from the mapping.

    convert_transaction() silently drops these, so without this the only symptom
    of a new card or account is transactions quietly not appearing in the budget.
    """
    counts: Dict[str, int] = {}
    for t in transactions:
        arrangement = t.get("arrangementId")
        if arrangement and arrangement not in mapping:
            counts[arrangement] = counts.get(arrangement, 0) + 1
    return counts


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
