import unittest
import json
from typing import Optional

import jsons


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
        result = json.loads(jsons.dumps(person))

        self.assertEqual(result["name"], "Bob")
        self.assertEqual(result["age"], 25)
        self.assertIsNone(result["email"])

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



if __name__ == '__main__':
    unittest.main(verbosity=2)
