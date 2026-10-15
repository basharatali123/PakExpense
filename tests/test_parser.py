"""
Comprehensive tests for Pakistani Financial SMS Parser & Database Operations.
"""
import os
import unittest
import tempfile
from core.parser import PakistanSMSParser
from core.db import DatabaseManager
from core.importer import SMSBatchImporter

class TestPakistanSMSParser(unittest.TestCase):

    def test_jazzcash_sent(self):
        sms = "You have sent Rs. 1500 to 03001234567 from your JazzCash Account. Fee Rs. 0.00. Balance: Rs. 14,250.00. Trx ID: 1234567890."
        res = PakistanSMSParser.parse_sms(sms, sender_id="8558")
        self.assertIsNotNone(res)
        self.assertEqual(res.provider, "JazzCash")
        self.assertEqual(res.trans_type, "Debit")
        self.assertEqual(res.amount, 1500.0)
        self.assertEqual(res.ref_id, "1234567890")
        self.assertEqual(res.balance_after, 14250.0)

    def test_jazzcash_received(self):
        sms = "You have received Rs. 5,000.00 from USMAN TARIQ (03019876543) in your JazzCash Account. Balance: Rs. 19,250.00. Trx ID: 5566778899."
        res = PakistanSMSParser.parse_sms(sms, sender_id="8558")
        self.assertIsNotNone(res)
        self.assertEqual(res.trans_type, "Credit")
        self.assertEqual(res.amount, 5000.0)
        self.assertEqual(res.ref_id, "5566778899")
        self.assertEqual(res.balance_after, 19250.0)

    def test_easypaisa_transfer(self):
        sms = "Transferred Rs. 2000 to BILAL SHAH (03451234567). Fee: Rs. 0. New balance is Rs. 8,500. Trx ID: 1029384756."
        res = PakistanSMSParser.parse_sms(sms, sender_id="3737")
        self.assertIsNotNone(res)
        self.assertEqual(res.provider, "EasyPaisa")
        self.assertEqual(res.trans_type, "Debit")
        self.assertEqual(res.amount, 2000.0)
        self.assertEqual(res.ref_id, "1029384756")
        self.assertEqual(res.balance_after, 8500.0)

    def test_easypaisa_received(self):
        sms = "You have received Rs. 4,500 from SAAD KHAN (03459876543). Your new balance is Rs. 13,000. Trx ID: 9081726354."
        res = PakistanSMSParser.parse_sms(sms, sender_id="3737")
        self.assertIsNotNone(res)
        self.assertEqual(res.trans_type, "Credit")
        self.assertEqual(res.amount, 4500.0)
        self.assertEqual(res.ref_id, "9081726354")
        self.assertEqual(res.balance_after, 13000.0)

    def test_bill_payment_category(self):
        sms = "Bill payment of Rs. 3,420 for LESCO was successful. Trx ID: 99881122. New Bal: Rs. 10,380."
        res = PakistanSMSParser.parse_sms(sms, sender_id="8558")
        self.assertIsNotNone(res)
        self.assertEqual(res.amount, 3420.0)
        self.assertIn("Bills & Utilities", res.category)

    def test_mobile_load(self):
        sms = "Paid Rs. 500 for mobile load to 03451122334. Trx ID: 8746352910."
        res = PakistanSMSParser.parse_sms(sms, sender_id="3737")
        self.assertIsNotNone(res)
        self.assertEqual(res.amount, 500.0)
        self.assertIn("Mobile Load", res.category)

    def test_meezan_bank(self):
        sms = "Dear Customer, your Account 01010102030405 has been debited by PKR 4,250.00 on 14-OCT-26 at SHELL PETROL PUMP. Available Balance is PKR 65,420.50. Ref: 261014123456."
        res = PakistanSMSParser.parse_sms(sms, sender_id="8267")
        self.assertIsNotNone(res)
        self.assertEqual(res.provider, "Meezan Bank")
        self.assertEqual(res.trans_type, "Debit")
        self.assertEqual(res.amount, 4250.0)
        self.assertEqual(res.balance_after, 65420.50)
        self.assertEqual(res.ref_id, "261014123456")
        self.assertIn("Fuel", res.category)

    def test_hbl_credit(self):
        sms = "Dear Customer, PKR 45,000.00 credited to your A/c ending 1234 on 05-Oct-26. Info: SALARY DEPOSIT. Avail Bal: PKR 87,100.00."
        res = PakistanSMSParser.parse_sms(sms, sender_id="4250")
        self.assertIsNotNone(res)
        self.assertEqual(res.provider, "HBL")
        self.assertEqual(res.trans_type, "Credit")
        self.assertEqual(res.amount, 45000.0)
        self.assertEqual(res.balance_after, 87100.0)
        self.assertIn("Salary", res.category)

    def test_user_actual_jazzcash_daewoo(self):
        sms = "Rs 1,610.00 paid to DAEWOO on 16-10-2026 at 00:27:16. Fee: Rs 0.00, TID:727238040565"
        res = PakistanSMSParser.parse_sms(sms, sender_id="8558")
        self.assertIsNotNone(res)
        self.assertEqual(res.provider, "JazzCash")
        self.assertEqual(res.amount, 1610.0)
        self.assertEqual(res.recipient_or_sender, "DAEWOO")
        self.assertEqual(res.ref_id, "727238040565")
        self.assertIn("Transport", res.category)

    def test_user_actual_meezan_pharmacy(self):
        sms = "PKR 8,371.00 charged at JINNAH PHARMACY for card used, from A/C xxx2120 (THOKAR NIAZ BAIG LHR) on 08-Oct-2026 at 05:08 TID:560755"
        res = PakistanSMSParser.parse_sms(sms, sender_id="8079")
        self.assertIsNotNone(res)
        self.assertEqual(res.provider, "Meezan Bank")
        self.assertEqual(res.amount, 8371.0)
        self.assertEqual(res.recipient_or_sender, "JINNAH PHARMACY")
        self.assertEqual(res.ref_id, "560755")
        self.assertIn("Health & Medical", res.category)

    def test_user_actual_meezan_atm(self):
        sms = "PKR 10,035.00 cash withdrawn from 1Link ATM from A/C xxx2120 THOKAR NIAZ BAIG LHR on 08-Oct-2026 at 05:24 TID:387289  UAN 021111331331"
        res = PakistanSMSParser.parse_sms(sms, sender_id="8079")
        self.assertIsNotNone(res)
        self.assertEqual(res.provider, "Meezan Bank")
        self.assertEqual(res.amount, 10035.0)
        self.assertEqual(res.recipient_or_sender, "1Link ATM")
        self.assertEqual(res.ref_id, "387289")
        self.assertIn("Cash Withdrawal", res.category)

    def test_user_actual_meezan_transfer(self):
        sms = "PKR 5,000.00 sent to BASHARAT ALI JAZZ-xxxCASH from your A/C xxx2120 on 12-Oct-2026 at 22:08 Fee: Rs.2.00 TID:353041 UAN 021111331331"
        res = PakistanSMSParser.parse_sms(sms, sender_id="8079")
        self.assertIsNotNone(res)
        self.assertEqual(res.provider, "Meezan Bank")
        self.assertEqual(res.amount, 5000.0)
        self.assertEqual(res.recipient_or_sender, "BASHARAT ALI JAZZ-xxxCASH")
        self.assertEqual(res.fee, 2.0)
        self.assertEqual(res.ref_id, "353041")

    def test_database_persistence(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db = f.name

        try:
            db = DatabaseManager(temp_db)
            accounts = db.get_accounts()
            self.assertGreater(len(accounts), 0)

            categories = db.get_categories()
            self.assertGreater(len(categories), 0)

            # Add transaction
            trans_id = db.add_transaction(
                account_id=accounts[0]["id"],
                category_id=categories[0]["id"],
                trans_date="2026-10-15 10:30",
                amount=2500.0,
                trans_type="Debit",
                recipient_or_sender="Test Vendor",
                description="Test Debit",
                ref_id="TESTREF999"
            )
            self.assertGreater(trans_id, 0)

            # Query transaction
            txs = db.get_transactions()
            self.assertEqual(len(txs), 1)
            self.assertEqual(txs[0]["amount"], 2500.0)
            self.assertEqual(txs[0]["ref_id"], "TESTREF999")

            # Check duplicate detection
            is_dup = db.check_duplicate_transaction("TESTREF999", 2500.0, "2026-10-15")
            self.assertTrue(is_dup)
        finally:
            if os.path.exists(temp_db):
                os.remove(temp_db)

if __name__ == "__main__":
    unittest.main()
