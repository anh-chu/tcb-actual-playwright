"""Private, durable bank observations. No credentials or HTTP headers are stored."""
import datetime
import json
import os
from pathlib import Path
from uuid import uuid4


def rows(body):
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        document = body.get("document")
        if isinstance(document, dict) and isinstance(document.get("listTransaction"), list):
            return document["listTransaction"]
        for key in ("transactions", "value", "data"):
            if isinstance(body.get(key), list):
                return body[key]
    raise ValueError("Unrecognized TCB transaction response; refusing incomplete audit/import")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Audit:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:12]
        self.directory = self.root / "runs" / self.run_id
        self.directory.mkdir(parents=True, mode=0o700)
        self.state = {"schema_version": 1, "run_id": self.run_id, "started_at": now(),
                      "source": "Techcombank authenticated API", "status": "fetching",
                      "actual_import_completed": False}
        self.update()

    def write(self, path, value):
        text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        temp = path.with_suffix(path.suffix + ".tmp")
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        if json.loads(path.read_text()) != value:
            raise OSError("Audit read-back failed")

    def record(self, name, value):
        self.write(self.directory / name, value)

    def update(self, **values):
        self.state.update(values)
        self.state["updated_at"] = now()
        self.record("manifest.json", self.state)
        self.write(self.root / "latest-attempt.json", self.state)

    def bank_snapshot(self, balances, transactions, date_from, date_to):
        observed = now()
        common = {"schema_version": 1, "run_id": self.run_id, "observed_at": observed,
                  "source": self.state["source"]}
        balance_doc = {**common, "accounts": balances}
        tx_doc = {**common, "date_from": date_from, "date_to": date_to,
                  "pagination_complete": True, "count": len(transactions), "transactions": transactions}
        self.record("balances.json", balance_doc)
        self.record("transactions-pre-actual.json", tx_doc)
        self.update(status="bank_captured", date_from=date_from, date_to=date_to,
                    transactions_fetched=len(transactions))
        # Single atomic pointer to the last complete bank snapshot. Failed runs do
        # not replace it. Always consult latest-attempt.json as well for freshness.
        self.write(self.root / "latest-bank.json", {**common, "directory": str(self.directory),
                   "balances_file": str(self.directory / "balances.json"),
                   "transactions_file": str(self.directory / "transactions-pre-actual.json")})
