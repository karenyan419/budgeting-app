import pytest
from datetime import date

from services.monzo_parser import parse_monzo_csv
from services.yonder_parser import parse_yonder_csv


class TestMonzoParser:
    def test_parse_single_transaction(self):
        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Card payment,Tesco,,Groceries,-25.50,GBP"""

        result = parse_monzo_csv(csv_content)

        assert len(result) == 1
        assert result[0]["date"] == date(2026, 2, 20)
        assert result[0]["description"] == "Tesco"
        assert result[0]["amount"] == -25.50
        assert result[0]["source_category"] == "Groceries"
        assert result[0]["hash"] is not None

    def test_parse_multiple_transactions(self):
        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Card payment,Tesco,,Groceries,-25.50,GBP
tx_002,21/02/2026,14:00:00,Card payment,TFL,,Transport,-5.00,GBP
tx_003,22/02/2026,09:00:00,Faster payment,Salary,,Income,3000.00,GBP"""

        result = parse_monzo_csv(csv_content)

        assert len(result) == 3
        assert result[0]["description"] == "Tesco"
        assert result[1]["description"] == "TFL"
        assert result[2]["description"] == "Salary"

    def test_parse_income_positive_amount(self):
        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Faster payment,Employer,,Income,2500.00,GBP"""

        result = parse_monzo_csv(csv_content)

        assert len(result) == 1
        assert result[0]["amount"] == 2500.00

    def test_empty_category(self):
        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Card payment,Random Shop,,,-15.00,GBP"""

        result = parse_monzo_csv(csv_content)

        assert len(result) == 1
        assert result[0]["source_category"] is None

    def test_hash_uniqueness(self):
        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Card payment,Tesco,,Groceries,-25.50,GBP
tx_002,20/02/2026,10:30:00,Card payment,Tesco,,Groceries,-25.50,GBP"""

        result = parse_monzo_csv(csv_content)

        # Same transaction details should produce same hash
        assert result[0]["hash"] == result[1]["hash"]

    def test_different_transactions_different_hash(self):
        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Card payment,Tesco,,Groceries,-25.50,GBP
tx_002,21/02/2026,10:30:00,Card payment,Tesco,,Groceries,-25.50,GBP"""

        result = parse_monzo_csv(csv_content)

        # Different dates should produce different hashes
        assert result[0]["hash"] != result[1]["hash"]

    def test_skip_invalid_rows(self):
        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,invalid_date,10:30:00,Card payment,Tesco,,Groceries,-25.50,GBP
tx_002,20/02/2026,10:30:00,Card payment,Valid,,Groceries,-10.00,GBP"""

        result = parse_monzo_csv(csv_content)

        assert len(result) == 1
        assert result[0]["description"] == "Valid"


class TestYonderParser:
    def test_parse_single_transaction(self):
        csv_content = """"Date/Time of transaction","Description","Amount (GBP)","Amount (in Charged Currency)","Currency","Category","Debit or Credit","Country"
"2026-03-18T13:55:20.413736","TFL - Transport for London","7.20","7.20","GBP","Transport","Debit","GBR\""""

        result = parse_yonder_csv(csv_content)

        assert len(result) == 1
        assert result[0]["date"] == date(2026, 3, 18)
        assert result[0]["description"] == "TFL - Transport for London"
        assert result[0]["amount"] == -7.20  # Debit should be negative
        assert result[0]["source_category"] == "Transport"

    def test_parse_multiple_transactions(self):
        csv_content = """"Date/Time of transaction","Description","Amount (GBP)","Amount (in Charged Currency)","Currency","Category","Debit or Credit","Country"
"2026-03-18T13:55:20.413736","TFL","7.20","7.20","GBP","Transport","Debit","GBR"
"2026-03-17T10:00:00.000000","Asda","30.00","30.00","GBP","Groceries","Debit","GBR\""""

        result = parse_yonder_csv(csv_content)

        assert len(result) == 2

    def test_debit_is_negative(self):
        csv_content = """"Date/Time of transaction","Description","Amount (GBP)","Amount (in Charged Currency)","Currency","Category","Debit or Credit","Country"
"2026-03-18T13:55:20.413736","Coffee Shop","5.00","5.00","GBP","Eating Out","Debit","GBR\""""

        result = parse_yonder_csv(csv_content)

        assert result[0]["amount"] == -5.00

    def test_skip_zero_amounts(self):
        csv_content = """"Date/Time of transaction","Description","Amount (GBP)","Amount (in Charged Currency)","Currency","Category","Debit or Credit","Country"
"2026-03-18T13:55:20.413736","Pending Auth","0","0","GBP","General","Debit","GBR"
"2026-03-18T14:00:00.000000","Real Purchase","10.00","10.00","GBP","General","Debit","GBR\""""

        result = parse_yonder_csv(csv_content)

        assert len(result) == 1
        assert result[0]["description"] == "Real Purchase"

    def test_hash_generation(self):
        csv_content = """"Date/Time of transaction","Description","Amount (GBP)","Amount (in Charged Currency)","Currency","Category","Debit or Credit","Country"
"2026-03-18T13:55:20.413736","TFL","7.20","7.20","GBP","Transport","Debit","GBR\""""

        result = parse_yonder_csv(csv_content)

        assert result[0]["hash"] is not None
        assert len(result[0]["hash"]) == 16
