import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from modules.audit import Audit, rows


class AuditTests(unittest.TestCase):
    def test_snapshot_survives_later_failure_and_is_private(self):
        with tempfile.TemporaryDirectory() as root:
            first = Audit(root)
            first.bank_snapshot([{"bank_response": {"bookedBalance": "123"}}], [{"id": "fixture"}], "2026-01-01", "2026-01-02")
            pointer = json.loads((Path(root) / "latest-bank.json").read_text())
            second = Audit(root)
            second.update(status="failed")
            self.assertEqual(json.loads((Path(root) / "latest-bank.json").read_text()), pointer)
            self.assertEqual(json.loads((Path(root) / "latest-attempt.json").read_text())["status"], "failed")
            self.assertEqual(os.stat(first.directory / "balances.json").st_mode & 0o777, 0o600)
            self.assertEqual(os.stat(root).st_mode & 0o777, 0o700)
            first.record("repeat.json", {"same": 1})
            first.record("repeat.json", {"same": 1})
            self.assertEqual(json.loads((first.directory / "repeat.json").read_text()), {"same": 1})

    def test_unknown_response_is_not_empty_success(self):
        with self.assertRaises(ValueError):
            rows({"error": "expired"})
        self.assertEqual(rows({"transactions": []}), [])


class FlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_paginated_capture_precedes_actual_and_survives_import_failure(self):
        from service import BankingService
        with tempfile.TemporaryDirectory() as root:
            svc = BankingService()
            svc._audit = Audit(root)
            svc._config = {"accounts_mapping": {"bank-fixture": "actual-fixture"},
                           "date_from": "2026-01-01", "date_to": "2026-01-02",
                           "actual_url": "fixture", "actual_password": "fixture", "actual_budget_id": "fixture"}
            svc._resolve_bearer_token = AsyncMock(return_value="TEST-ONLY")
            def response(body, status=200):
                return SimpleNamespace(status=status, text=AsyncMock(return_value=json.dumps(body)))
            request = SimpleNamespace(post=AsyncMock(return_value=response({})), get=AsyncMock(side_effect=[
                response({"bookedBalance": "123"}), response([{"id": str(n)} for n in range(500)]), response([{"id": "500"}])]))
            svc._page = SimpleNamespace(request=request)
            def actual_init(config):
                self.assertTrue((svc._audit.directory / "transactions-pre-actual.json").is_file())
                self.assertTrue((svc._audit.directory / "actual-payload.json").is_file())
                doc = json.loads((svc._audit.directory / "transactions-pre-actual.json").read_text())
                self.assertEqual(doc["count"], 501)
                raise RuntimeError("fixture Actual unavailable")
            with patch("service.convert.unmapped_arrangements", return_value={}), patch("service.convert.convert_to_transactions", return_value={"actual-fixture": [{"id": "fixture"}]}), patch("service.actual.init_actual", side_effect=actual_init):
                with self.assertRaisesRegex(RuntimeError, "fixture Actual unavailable"):
                    await svc._process_fetch()
            self.assertIn("from=500", request.get.call_args_list[-1].kwargs["url"])
            self.assertTrue((Path(root) / "latest-bank.json").is_file())
            self.assertFalse(svc._audit.state["actual_import_completed"])

    async def test_401_blocks_actual_and_snapshot_publication(self):
        from service import BankingService
        with tempfile.TemporaryDirectory() as root:
            svc = BankingService()
            svc._audit = Audit(root)
            svc._config = {"accounts_mapping": {"fixture": "fixture"}}
            svc._resolve_bearer_token = AsyncMock(return_value="TEST-ONLY")
            svc._page = SimpleNamespace(request=SimpleNamespace(post=AsyncMock(return_value=SimpleNamespace(status=401))))
            svc._process_save = AsyncMock()
            with self.assertRaisesRegex(Exception, "authentication rejected"):
                await svc._process_fetch()
            svc._process_save.assert_not_called()
            self.assertFalse((Path(root) / "latest-bank.json").exists())

    async def test_audit_write_failure_blocks_actual(self):
        from service import BankingService
        with tempfile.TemporaryDirectory() as root:
            svc = BankingService()
            svc._audit = Audit(root)
            svc._config = {"accounts_mapping": {}}
            with patch("service.convert.unmapped_arrangements", return_value={}), patch("service.convert.convert_to_transactions", return_value={}), patch.object(svc._audit, "record", side_effect=OSError("fixture disk full")), patch("service.actual.init_actual") as init:
                with self.assertRaises(OSError):
                    await svc._process_save("[]")
                init.assert_not_called()


if __name__ == "__main__":
    unittest.main()
