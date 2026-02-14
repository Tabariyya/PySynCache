import os
import time
import unittest

from SynCache.Cache import Cache


class Person:
    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name


class TestController(unittest.TestCase):

    def setUp(self):
        """Set up test environment before each test"""
        Cache.initialize(os.environ.get("BROKER_TOKEN"),
                         100)
        self.controller = Cache.get_instance()

    def tearDown(self):
        """Clean up after each test"""
        self.controller.evict_all()

    def test_reading(self):
        """Test the reading method"""

        self.controller.set("ns", "1", Person(first_name="Waleed", last_name="Shanaa"))

        person = self.controller.get("ns", "1", Person)
        self.assertEqual(person.first_name, "Waleed")

    def test_benchmark_reading_speed(self):
        """Test the reading method"""

        self.controller.set("ns", "1", Person(first_name="Waleed", last_name="Shanaa"))

        for i in range(25000):
            self.controller.get("ns", "1")
        start = time.time()
        for i in range(25000):
            self.controller.get("ns", "1")
        print("after getting string")
        end = time.time()
        elapsed = end - start
        print("Elapsed time: " + str(elapsed * 1000))

    def test_namespace_and_id_not_string(self):

        self.controller.set(1.5, 1, Person(first_name="Waleed", last_name="Shanaa"))
        person = self.controller.get(1.5, 1, Person)
        self.assertEqual(person.first_name, "Waleed")
        person = self.controller.get("1.5", "1", Person)
        self.assertEqual(person.first_name, "Waleed")

    def test_set_with_ttl(self):
        """Test setting values with time-to-live"""
        ttl = 10
        person = Person(first_name="John", last_name="Doe")

        self.controller.set("test_ns", "ttl_key", person, ttl)
        retrieved = self.controller.get("test_ns", "ttl_key", Person)

        self.assertEqual(retrieved.first_name, "John")
        self.assertEqual(retrieved.last_name, "Doe")

    def test_get_nonexistent_key(self):
        """Test retrieving a key that doesn't exist"""
        result = self.controller.get("nonexistent_ns", "nonexistent_key")
        self.assertIsNone(result)

    def test_overwrite_existing_key(self):
        """Test overwriting an existing key"""
        person1 = Person(first_name="Alice", last_name="Smith")
        person2 = Person(first_name="Bob", last_name="Johnson")

        self.controller.set("ns", "key1", person1)
        self.controller.set("ns", "key1", person2)

        result = self.controller.get("ns", "key1", Person)
        self.assertEqual(result.first_name, "Bob")
        self.assertEqual(result.last_name, "Johnson")

    def test_evict_specific_key(self):
        """Test evicting a specific key"""
        person = Person(first_name="Test", last_name="User")

        self.controller.set("ns", "key1", person)
        self.controller.set("ns", "key2", person)

        # Key should exist before eviction
        result1 = self.controller.get("ns", "key1", Person)
        self.assertIsNotNone(result1)

        # Evict key1
        self.controller.evict("ns", "key1")

        # Key1 should be gone, key2 should still exist
        result1_after = self.controller.get("ns", "key1")
        result2_after = self.controller.get("ns", "key2", Person)

        self.assertIsNone(result1_after)
        self.assertIsNotNone(result2_after)
        self.assertEqual(result2_after.first_name, "Test")

    def test_evict_namespace(self):
        """Test evicting an entire namespace"""
        person = Person(first_name="Test", last_name="User")

        self.controller.set("ns1", "key1", person)
        self.controller.set("ns1", "key2", person)
        self.controller.set("ns2", "key1", person)

        # Evict namespace ns1
        self.controller.evict_namespace("ns1")

        # ns1 keys should be gone
        self.assertIsNone(self.controller.get("ns1", "key1"))
        self.assertIsNone(self.controller.get("ns1", "key2"))

        # ns2 key should still exist
        result_ns2 = self.controller.get("ns2", "key1", Person)
        self.assertIsNotNone(result_ns2)
        self.assertEqual(result_ns2.first_name, "Test")

    def test_evict_all(self):
        """Test evicting all namespaces"""
        person = Person(first_name="Test", last_name="User")

        self.controller.set("ns1", "key1", person)
        self.controller.set("ns2", "key1", person)
        self.controller.set("ns3", "key1", person)

        # Evict all
        self.controller.evict_all()

        # All keys should be gone
        self.assertIsNone(self.controller.get("ns1", "key1"))
        self.assertIsNone(self.controller.get("ns2", "key1"))
        self.assertIsNone(self.controller.get("ns3", "key1"))

    def test_get_without_return_type(self):
        """Test get method without specifying return type"""
        person = Person(first_name="Jane", last_name="Smith")

        self.controller.set("ns", "key1", person)
        result_json = self.controller.get("ns", "key1")  # No return type

        # Should return JSON string
        self.assertIsInstance(result_json, str)
        self.assertIn("first_name", result_json)
        self.assertIn("Jane", result_json)
        self.assertIn("last_name", result_json)
        self.assertIn("Smith", result_json)

    def test_edge_case_namespace_id_types(self):
        """Test with various edge case types for namespace and id"""
        test_cases = [
            ("", "empty_namespace"),  # Empty namespace
            ("key", ""),  # Empty id
            ("space ns", "space key"),  # Namespace with spaces
            ("ns@#$", "key!@#"),  # Special characters
            ("very_long_namespace_" * 10, "key"),  # Long namespace
            ("ns", "very_long_key_" * 100),  # Long key
        ]

        person = Person(first_name="Edge", last_name="Case")

        for namespace, id_value in test_cases:
            with self.subTest(namespace=namespace, id=id_value):
                self.controller.set(namespace, id_value, person)
                result = self.controller.get(namespace, id_value, Person)
                self.assertEqual(result.first_name, "Edge")
                self.assertEqual(result.last_name, "Case")

    def test_concurrent_access(self):
        """Simulate concurrent access patterns"""
        import threading

        results = []
        errors = []

        def worker(thread_id):
            try:
                person = Person(first_name=f"Thread{thread_id}", last_name="Worker")
                self.controller.set("concurrent_ns", f"key_{thread_id}", person)

                # Small delay
                time.sleep(0.001)

                result = self.controller.get("concurrent_ns", f"key_{thread_id}", Person)
                results.append((thread_id, result.first_name))
            except Exception as e:
                errors.append(str(e))

        # Create multiple threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify all threads completed successfully
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 10)

        # Verify data integrity
        for thread_id, first_name in results:
            self.assertEqual(first_name, f"Thread{thread_id}")

    def test_cache_expiration(self):
        """Test that entries expire when TTL is reached"""
        # Set with short TTL
        self.controller.set("expire_ns", "key1", Person(first_name="Temp", last_name="User"), 1)

        # Should exist immediately
        result = self.controller.get("expire_ns", "key1", Person)
        self.assertEqual(result.first_name, "Temp")

        # Wait for expiration
        time.sleep(2)

        # Should be expired
        result = self.controller.get("expire_ns", "key1")
        self.assertIsNone(result)

    def test_memory_limits(self):
        """Test behavior when reaching max_entries limit"""
        # We have max_entries=100, try to add more
        for i in range(110):
            person = Person(first_name=f"Person{i}", last_name="Test")
            self.controller.set("limit_ns", f"key{i}", person)

        # Should still be able to retrieve some keys
        # (Note: actual eviction policy depends on _Controller implementation)
        result = self.controller.get("limit_ns", "key0", Person)
        # This might be None if LRU eviction happened

        # At minimum, recent keys should exist
        result_recent = self.controller.get("limit_ns", "key109", Person)
        self.assertIsNotNone(result_recent)
        self.assertEqual(result_recent.first_name, "Person109")

    def test_setting_string(self):
        self.controller.set("ns1", "key1", "waleed")
        result = self.controller.get("ns1", "key1")
        self.assertEqual(result, "waleed")

    def test_setting_integer(self):
        self.controller.set("ns1", "key1", 5)
        result = self.controller.get("ns1", "key1", int)
        self.assertEqual(result, 5)

    def test_setting_float(self):
        self.controller.set("ns1", "key1", 5.5)
        result = self.controller.get("ns1", "key1", float)
        self.assertEqual(result, 5.5)

    def test_setting_boolean(self):
        self.controller.set("ns1", "key1", True)
        result = self.controller.get("ns1", "key1", bool)
        self.assertEqual(result, True)

    def test_setting_none(self):
        self.controller.set("ns1", "key1", None)
        result = self.controller.get("ns1", "key1")
        self.assertEqual(result, None)


if __name__ == '__main__':
    unittest.main(verbosity=2)
