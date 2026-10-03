import unittest
from unittest import mock

from modules import convert

MAP = {"arr1": "acct1"}


def tx(amount, cur, ci, desc, tid="t1"):
    return {
        "id": tid, "arrangementId": "arr1", "bookingDate": "2026-10-02",
        "transactionAmountCurrency": {"amount": amount, "currencyCode": cur},
        "creditDebitIndicator": ci, "description": desc,
    }


class FxConvertTest(unittest.TestCase):
    def test_uses_bank_settled_vnd(self):
        d = "Giao dich thanh toan/ Purchase - So The/Card No:...1472 Twitch Interactive, Inc. So tien sau khi quy doi: 205958 VND"
        with mock.patch.object(convert, "get_exchange_rate") as rate:
            out = convert.convert_transaction(tx("7.87", "USD", "DBIT", d), MAP)
        self.assertEqual(out["amount"], -20595800)
        rate.assert_not_called()

    def test_falls_back_to_rate_without_settled_amount(self):
        d = "Giao dich hoan tra/revert - So The/Card No:...1472 GRAB"
        with mock.patch.object(convert, "get_exchange_rate", return_value=414.0) as rate:
            out = convert.convert_transaction(tx("533.54", "PHP", "CRDT", d), MAP)
        self.assertEqual(out["amount"], round(533.54 * 414.0 * 100))
        rate.assert_called_once_with("PHP")

    def test_vnd_rows_untouched(self):
        d = "Giao dich thanh toan/Purchase - So The/Card No:...1472 PAYOO*HDL"
        with mock.patch.object(convert, "get_exchange_rate") as rate:
            out = convert.convert_transaction(tx("1117800", "VND", "DBIT", d), MAP)
        self.assertEqual(out["amount"], -111780000)
        rate.assert_not_called()

    def test_vnd_row_ignores_settled_text(self):
        d = "Thanh toan no the tin dung - So tien 3714654 VND - Ngay 22/09/2026 quy doi: 1 VND"
        out = convert.convert_transaction(tx("3714654", "VND", "CRDT", d), MAP)
        self.assertEqual(out["amount"], 371465400)

    def test_settled_vnd_parser(self):
        self.assertEqual(convert.settled_vnd("x So tien sau khi quy doi: 6017451 VND"), 6017451)
        self.assertIsNone(convert.settled_vnd("no conversion here"))
        self.assertIsNone(convert.settled_vnd(None))


if __name__ == "__main__":
    unittest.main()
