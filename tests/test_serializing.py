import unittest
import json
from typing import Optional
from unittest.mock import patch
import datetime

import jsons

from SynCache.Serializable import to_epoch


class TestSerializable(unittest.TestCase):
    """Test the Serializable base class"""

    def setUp(self):
        class Person:
            def __init__(self, name: str, age: int, email: Optional[str] = None):
                self.name = name
                self.age = age
                self.email = email
                self._private_attr = "secret"  # This should be included in to_json

        class Product:
            def __init__(self, id: int, name: str, price: float, *args, **kwargs):
                self.id = id
                self.name = name
                self.price = price
                self.extra_args = args
                self.extra_kwargs = kwargs

        self.Person = Person
        self.Product = Product

    def test_to_json_basic(self):
        """Test basic to_json functionality"""
        person = self.Person("Alice", 30, "alice@example.com")
        result = json.loads(jsons.dumps(person))

        self.assertEqual(result["name"], "Alice")
        self.assertEqual(result["age"], 30)
        self.assertEqual(result["email"], "alice@example.com")
        self.assertEqual(result["_private_attr"], "secret")

    def test_to_json_with_defaults(self):
        """Test to_json with optional parameters"""
        person = self.Person("Bob", 25)  # email omitted
        # result = json.loads(person.model_dump_json())
        #
        # self.assertEqual(result["name"], "Bob")
        # self.assertEqual(result["age"], 25)
        # self.assertIsNone(result["email"])

    def test_from_json_basic(self):
        """Test basic from_json functionality"""
        json_str = '{"name": "Charlie", "age": 35, "email": "charlie@example.com"}'
        person = jsons.loads(json_str, self.Person)

        self.assertEqual(person.name, "Charlie")
        self.assertEqual(person.age, 35)
        self.assertEqual(person.email, "charlie@example.com")

    def test_from_json_with_missing_fields(self):
        """Test from_json with fields missing from JSON"""
        # age is a required parameter but missing from JSON
        json_str = '{"name": "David"}'
        with self.assertRaises(ValueError):
            jsons.loads(json_str, self.Person)

    def test_from_json_with_extra_fields(self):
        """Test from_json with extra fields in JSON"""
        json_str = '{"name": "Eve", "age": 28, "email": "eve@example.com", "extra": "ignored"}'
        person = jsons.loads(json_str, self.Person)

        self.assertEqual(person.name, "Eve")
        self.assertEqual(person.age, 28)
        self.assertEqual(person.email, "eve@example.com")
        # Extra field is not in __init__ signature, so it's ignored

    def test_from_json_with_args_kwargs(self):
        """Test from_json with *args and **kwargs in constructor"""
        product = self.Product(1, "Widget", 19.99, "extra_arg", category="tools")
        json_str = jsons.dumps(product)
        product2 = jsons.loads(json_str, self.Product)

        self.assertEqual(product2.id, 1)
        self.assertEqual(product2.name, "Widget")
        self.assertEqual(product2.price, 19.99)

    def test_round_trip(self):
        """Test serialization/deserialization round trip"""
        original = self.Person("Frank", 40, "frank@example.com")
        original._private_attr = "modified"

        json_str = jsons.dumps(original)
        restored = jsons.loads(json_str, self.Person)

        self.assertEqual(original.name, restored.name)
        self.assertEqual(original.age, restored.age)
        self.assertEqual(original.email, restored.email)
        self.assertEqual(original._private_attr, restored._private_attr)

    def test_invalid_json(self):
        """Test from_json with invalid JSON"""
        with self.assertRaises(json.JSONDecodeError):
            jsons.loads("invalid json", self.Person)


class TestToEpoch(unittest.TestCase):
    """Test the to_epoch function"""

    def test_none(self):
        """Test None input"""
        self.assertIsNone(to_epoch(None))

    def test_int_epoch(self):
        """Test integer epoch input"""
        epoch = 1672531200  # 2023-01-01 00:00:00 UTC
        result = to_epoch(epoch)

        self.assertEqual(result, epoch)
        self.assertIsInstance(result, int)

    def test_float_epoch(self):
        """Test float epoch input"""
        epoch = 1672531200.5
        result = to_epoch(epoch)

        self.assertEqual(result, 1672531200)  # Truncated to int
        self.assertIsInstance(result, int)

    def test_datetime_naive(self):
        """Test naive datetime (assumed UTC)"""
        dt = datetime.datetime(2023, 1, 1, 12, 0, 0)
        result = to_epoch(dt)

        expected = int(dt.replace(tzinfo=datetime.timezone.utc).timestamp())
        self.assertEqual(result, expected)

    def test_datetime_aware(self):
        """Test timezone-aware datetime"""
        from datetime import timezone, timedelta

        # UTC datetime
        dt_utc = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result_utc = to_epoch(dt_utc)

        # UTC+2 datetime (should convert to same epoch as UTC)
        tz_offset = timezone(timedelta(hours=2))
        dt_offset = datetime.datetime(2023, 1, 1, 14, 0, 0, tzinfo=tz_offset)
        result_offset = to_epoch(dt_offset)

        self.assertEqual(result_utc, result_offset)

    def test_date(self):
        """Test date object (midnight UTC)"""
        d = datetime.date(2023, 1, 1)
        result = to_epoch(d)

        dt = datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        expected = int(dt.timestamp())
        self.assertEqual(result, expected)

    @patch('time.time')
    def test_timedelta(self, mock_time):
        """Test timedelta (relative to now)"""
        mock_time.return_value = 1672531200.0  # Fixed "now"

        td = datetime.timedelta(hours=1)
        result = to_epoch(td)

        expected = 1672531200 + 3600
        self.assertEqual(result, expected)

    @patch('time.time')
    def test_timedelta_days(self, mock_time):
        """Test timedelta with days"""
        mock_time.return_value = 1672531200.0

        td = datetime.timedelta(days=1, hours=6)
        result = to_epoch(td)

        expected = 1672531200 + (24 + 6) * 3600
        self.assertEqual(result, expected)

    def test_invalid_datetime_string(self):
        """Test invalid datetime string"""
        with self.assertRaises(ValueError):
            to_epoch("not a date")

    def test_invalid_type(self):
        """Test invalid input type"""
        with self.assertRaises(ValueError):
            to_epoch([])  # List is not supported

        with self.assertRaises(ValueError):
            to_epoch({})  # Dict is not supported


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple functions"""

    def test_ttl_in_future(self):
        """Test that TTL conversion produces future timestamps"""
        with patch('time.time', return_value=1672531200.0):
            # Various future TTL formats
            test_cases = [
                (datetime.timedelta(hours=1), 1672531200 + 3600),
                (1672531200 + 3600, 1672531200 + 3600),  # Already epoch
            ]

            for ttl, expected in test_cases:
                result = to_epoch(ttl)
                self.assertGreater(result, 1672531200, f"Failed for: {ttl}")
                self.assertEqual(result, expected, f"Failed for: {ttl}")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""

    def test_serializable_empty_object(self):
        """Test Serializable with no attributes"""

        class Empty:
            def __init__(self):
                pass

        obj = Empty()
        json_str = jsons.dumps(obj)
        self.assertEqual(json_str, '{}')

        restored = jsons.loads(json_str, Empty)
        self.assertIsInstance(restored, Empty)

    def test_to_epoch_fractional_seconds(self):
        """Test that fractional seconds are handled correctly"""
        epoch_float = 1672531200.999
        result = to_epoch(epoch_float)

        self.assertEqual(result, 1672531200)  # Truncated, not rounded

    def test_to_epoch_large_values(self):
        """Test very large epoch values"""
        large_epoch = 9999999999  # Year 2286
        result = to_epoch(large_epoch)

        self.assertEqual(result, large_epoch)

    def test_to_epoch_zero(self):
        """Test zero and negative epoch values"""
        self.assertEqual(to_epoch(0), 0)
        self.assertEqual(to_epoch(-100), -100)


if __name__ == '__main__':
    unittest.main(verbosity=2)
