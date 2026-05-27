import os
import unittest

from SynCache.Cache import Cache
from SynCache.decorators import _eval_expr, cacheable, cache_put, cache_evict


class Person:
    def __init__(self, first_name, last_name, id=None):
        self.first_name = first_name
        self.last_name = last_name
        self.id = id

    def __eq__(self, other):
        if not isinstance(other, Person):
            return False
        return (self.first_name == other.first_name and
                self.last_name == other.last_name and
                self.id == other.id)


class TestEvaluatingExpressions(unittest.TestCase):

    def test_eval_expr_plain_string(self):
        """Test non-expression string returns as is"""
        result = _eval_expr("plain_string", (), {}, None)
        self.assertEqual(result, "plain_string")

    def test_eval_expr_kwarg(self):
        """Test expression with keyword argument"""
        kwargs = {"user_id": 123, "name": "John"}
        result = _eval_expr("#user_id", (), kwargs, None)
        self.assertEqual(result, "123")

    def test_eval_expr_object_attribute(self):
        """Test expression with object attribute access"""

        class User:
            def __init__(self):
                self.id = 456
                self.name = "Jane"

        user = User()
        kwargs = {"user": user}
        result = _eval_expr("#user.id", (), kwargs, None)
        self.assertEqual(result, "456")

        result = _eval_expr("#user.name", (), kwargs, None)
        self.assertEqual(result, "Jane")

        result = _eval_expr("#user.name-#user.id", (), kwargs, None)
        self.assertEqual(result, "Jane-456")

    def test_eval_expr_result_attribute(self):
        """Test expression with result object attribute access"""

        class Result:
            def __init__(self):
                self.id = 789
                self.data = "result_data"

        result_obj = Result()
        result = _eval_expr("#result.id", (), {}, result_obj)
        self.assertEqual(result, "789")

    def test_eval_expr_nested_attribute(self):
        """Test expression with nested attribute access"""

        class Profile:
            def __init__(self):
                self.user = type('User', (), {'id': 999})()

        profile = Profile()
        kwargs = {"profile": profile}
        result = _eval_expr("#profile.user.id", (), kwargs, None)
        self.assertEqual(result, "999")

    def test_eval_expr_dict_access(self):
        """Test expression with dictionary access"""
        data = {"id": 111, "name": "DictUser", "meta": {"role": "admin"}}
        kwargs = {"data": data}
        result = _eval_expr("#data.id", (), kwargs, None)
        self.assertEqual(result, "111")

        result = _eval_expr("#data.meta.role", (), kwargs, None)
        self.assertEqual(result, "admin")


class TestCacheableDecorator(unittest.TestCase):
    """Test Cacheable decorator functionality"""

    def setUp(self):
        """Set up test environment"""
        Cache.initialize(
            os.environ.get("BROKER_TOKEN"),
            100)
        self.controller = Cache.get_instance()

    def tearDown(self):
        """Clean up after each test"""
        self.controller.evict_all()

    def test_cacheable_simple_function(self):
        """Test Cacheable with simple function"""
        call_count = {"count": 0}

        @cacheable(namespace="test_ns", key="#user_id", return_type=Person)
        def get_user(user_id):
            call_count["count"] += 1
            return Person(first_name=f"User{user_id}", last_name="Doe")

        result1 = get_user(user_id=123)
        self.assertEqual(call_count["count"], 1)
        self.assertEqual(result1.first_name, "User123")

        result2 = get_user(user_id=123)
        self.assertEqual(call_count["count"], 1)  # No increment
        self.assertEqual(result2.first_name, "User123")

        # Third call with different params - should execute again
        result3 = get_user(user_id=456)
        self.assertEqual(call_count["count"], 2)
        self.assertEqual(result3.first_name, "User456")

    def test_cacheable_with_object_param(self):
        """Test Cacheable with object parameter"""
        call_count = {"count": 0}

        @cacheable(namespace="users", key="#user.id")
        def get_user_details(user):
            call_count["count"] += 1
            return f"Details for {user.first_name} {user.last_name}"

        user1 = Person(first_name="John", last_name="Doe", id=1)
        user2 = Person(first_name="Jane", last_name="Smith", id=2)

        result1 = get_user_details(user=user1)
        self.assertEqual(call_count["count"], 1)
        self.assertEqual(result1, "Details for John Doe")

        result2 = get_user_details(user=user1)
        self.assertEqual(call_count["count"], 1)
        self.assertEqual(result2, "Details for John Doe")
        #
        result3 = get_user_details(user=user2)
        self.assertEqual(call_count["count"], 2)
        self.assertEqual(result3, "Details for Jane Smith")

    def test_cacheable_with_kwargs(self):
        """Test Cacheable with keyword arguments"""
        call_count = {"count": 0}

        @cacheable(namespace="products", key="#product_id", return_type=dict)
        def get_product(product_id, category="default"):
            call_count["count"] += 1
            return {"id": product_id, "category": category, "name": f"Product{product_id}"}

        # Call with positional argument
        result1 = get_product(product_id=100)
        self.assertEqual(call_count["count"], 1)
        self.assertEqual(result1["id"], 100)

        # Same call should be cached (ignore category param in key)
        result2 = get_product(product_id=100, category="electronics")
        self.assertEqual(call_count["count"], 1)  # Still cached!
        self.assertEqual(result2["category"], "default")  # Returns cached version!

        # Different product_id
        result3 = get_product(product_id=200, category="books")
        self.assertEqual(call_count["count"], 2)
        self.assertEqual(result3["category"], "books")

    def test_cacheable_with_complex_key(self):
        """Test Cacheable with complex key expression"""
        call_count = {"count": 0}

        @cacheable(namespace="orders", key="#user.id-#order_type", return_type=dict)
        def get_order(user, order_type):
            call_count["count"] += 1
            return {"user_id": user.id, "order_type": order_type, "data": "order_data"}

        user = Person(first_name="Test", last_name="User", id=789)

        result1 = get_order(user=user, order_type="pending")
        self.assertEqual(call_count["count"], 1)

        result2 = get_order(user=user, order_type="pending")
        self.assertEqual(call_count["count"], 1)

        result3 = get_order(user=user, order_type="completed")
        self.assertEqual(call_count["count"], 2)

    def test_cacheable_with_complex_key2(self):
        """Test Cacheable with complex key expression"""
        call_count = {"count": 0}

        @cacheable(namespace="orders", key="#user.id#order_type", return_type=dict)
        def get_order(user, order_type):
            call_count["count"] += 1
            return {"user_id": user.id, "order_type": order_type, "data": "order_data"}

        user = Person(first_name="Test", last_name="User", id=789)

        result1 = get_order(user=user, order_type="pending")
        self.assertEqual(call_count["count"], 1)

        result2 = get_order(user=user, order_type="pending")
        self.assertEqual(call_count["count"], 1)

        result3 = get_order(user=user, order_type="completed")
        self.assertEqual(call_count["count"], 2)

    def test_cacheable_with_complex_key3(self):
        """Test Cacheable with complex key expression"""
        call_count = {"count": 0}

        @cacheable(namespace="orders", key="#user.id&#order_type", return_type=dict)
        def get_order(user, order_type):
            call_count["count"] += 1
            return {"user_id": user.id, "order_type": order_type, "data": "order_data"}

        user = Person(first_name="Test", last_name="User", id=789)

        result1 = get_order(user=user, order_type="pending")
        self.assertEqual(call_count["count"], 1)

        result2 = get_order(user=user, order_type="pending")
        self.assertEqual(call_count["count"], 1)

        result3 = get_order(user=user, order_type="completed")
        self.assertEqual(call_count["count"], 2)


class TestCachePutDecorator(unittest.TestCase):
    """Test CachePut decorator functionality"""

    def setUp(self):
        """Set up test environment"""
        Cache.initialize(
            os.environ.get("BROKER_TOKEN"),
            100)
        self.controller = Cache.get_instance()

    def tearDown(self):
        """Clean up after each test"""
        self.controller.evict_all()

    def test_cache_put_simple_function(self):
        """Test CachePut with simple function - should always execute and cache"""
        call_count = {"count": 0}

        # First define a cacheable function
        @cacheable(namespace="users", key="#user_id", return_type=Person)
        def get_user_cached(user_id):
            call_count["count"] += 1
            return Person(first_name=f"User{user_id}", last_name="Doe")

        # Then define a cache_put function that updates the cache
        @cache_put(namespace="users", key="#user_id")
        def update_user(user_id, first_name):
            return Person(first_name=first_name, last_name="Updated")

        # First call to cacheable - should execute
        result1 = get_user_cached(user_id=123)
        self.assertEqual(call_count["count"], 1)
        self.assertEqual(result1.first_name, "User123")

        # Second call to cacheable - should use cache
        result2 = get_user_cached(user_id=123)
        self.assertEqual(call_count["count"], 1)
        self.assertEqual(result2.first_name, "User123")

        # Call cache_put - should execute and update cache
        result3 = update_user(user_id=123, first_name="Modified")
        self.assertEqual(result3.first_name, "Modified")

        # Call cacheable again - should now return updated value from cache
        result4 = get_user_cached(user_id=123)
        self.assertEqual(call_count["count"], 1)  # Still 1 - retrieved from updated cache
        self.assertEqual(result4.first_name, "Modified")  # Updated value!

    def test_cache_put_with_object_param(self):
        """Test CachePut with object parameter"""
        call_count = {"count": 0}

        # Cacheable function
        @cacheable(namespace="user_details", key="#user.id")
        def get_user_details_cached(user):
            call_count["count"] += 1
            return f"Details for {user.first_name} {user.last_name}"

        # CachePut function
        @cache_put(namespace="user_details", key="#user.id")
        def update_user_details(user, new_role):
            return f"Details for {user.first_name} {user.last_name} - {new_role}"

        user = Person(first_name="John", last_name="Doe", id=1)

        # First call - cacheable executes
        result1 = get_user_details_cached(user=user)
        self.assertEqual(call_count["count"], 1)
        self.assertEqual(result1, "Details for John Doe")

        # Second call - from cache
        result2 = get_user_details_cached(user=user)
        self.assertEqual(call_count["count"], 1)

        # Update via cache_put
        result3 = update_user_details(user=user, new_role="Admin")
        self.assertEqual(result3, "Details for John Doe - Admin")

        # Should now get updated value from cache
        result4 = get_user_details_cached(user=user)
        self.assertEqual(call_count["count"], 1)
        self.assertEqual(result4, "Details for John Doe - Admin")

    def test_cache_put_always_executes(self):
        """Test that CachePut always executes the function, regardless of cache state"""
        call_count = {"count": 0}

        @cache_put(namespace="always_execute", key="#param")
        def always_execute_func(param):
            call_count["count"] += 1
            return f"Result: {param}"

        # Multiple calls should always increment counter
        result1 = always_execute_func(param="first")
        self.assertEqual(call_count["count"], 1)

        result2 = always_execute_func(param="first")  # Same param
        self.assertEqual(call_count["count"], 2)  # Still executes!

        result3 = always_execute_func(param="second")
        self.assertEqual(call_count["count"], 3)

    def test_cache_put_with_result_in_key(self):
        """Test CachePut using result in key expression"""
        call_count = {"count": 0}

        @cache_put(namespace="products", key="#result.id")
        def create_product(name, price):
            call_count["count"] += 1
            return {"id": hash(name), "name": name, "price": price}

        # Cacheable function to retrieve
        @cacheable(namespace="products", key="#product_id", return_type=dict)
        def get_product_cached(product_id):
            return {"id": product_id, "name": "Not Found"}

        # Create product - caches with key based on result
        result = create_product(name="Laptop", price=999)
        product_id = result["id"]

        # Should be able to retrieve using cacheable
        retrieved = get_product_cached(product_id=product_id)
        self.assertEqual(retrieved["name"], "Laptop")
        self.assertEqual(retrieved["price"], 999)

    def test_cache_put_with_complex_key_expression(self):
        """Test CachePut with complex key expressions"""

        @cache_put(namespace="orders", key="#user.id-#result.order_id")
        def create_order(user, order_data):
            import random
            return {
                "user_id": user.id,
                "order_id": random.randint(1000, 9999),
                "data": order_data
            }

        @cacheable(namespace="orders", key="#key", return_type=dict)
        def get_order_cached(key):
            return None

        user = Person(first_name="Test", last_name="User", id=123)

        # Create order
        result = create_order(user=user, order_data={"items": ["item1", "item2"]})
        cache_key = f"{user.id}-{result['order_id']}"

        # Should be retrievable
        retrieved = get_order_cached(key=cache_key)
        self.assertEqual(retrieved["user_id"], 123)
        self.assertEqual(retrieved["data"]["items"], ["item1", "item2"])

    def test_cache_put_with_multiple_namespaces(self):
        """Test CachePut updating multiple namespaces"""

        @cache_put(namespace="namespace1", key="#id")
        @cache_put(namespace="namespace2", key="#id")
        def update_both_namespaces(id, value):
            return {"id": id, "value": value}

        @cacheable(namespace="namespace1", key="#key", return_type=dict)
        def get_from_ns1(key):
            return None

        @cacheable(namespace="namespace2", key="#key", return_type=dict)
        def get_from_ns2(key):
            return None

        # Update both namespaces
        result = update_both_namespaces(id=123, value="test_value")

        # Verify both namespaces were updated
        from_ns1 = get_from_ns1(key=123)
        from_ns2 = get_from_ns2(key=123)

        self.assertEqual(from_ns1["value"], "test_value")
        self.assertEqual(from_ns2["value"], "test_value")

    def test_cache_put_with_existing_cache(self):
        """Test CachePut overwrites existing cache entries"""

        # First populate cache
        @cacheable(namespace="test_overwrite", key="#id", return_type=str)
        def get_value_cached(id):
            return f"original_{id}"

        @cache_put(namespace="test_overwrite", key="#id")
        def update_value(id, new_value):
            return f"updated_{id}_{new_value}"

        # Get original value
        original = get_value_cached(id=1)
        self.assertEqual(original, "original_1")

        # Update with cache_put
        updated = update_value(id=1, new_value="new")
        self.assertEqual(updated, "updated_1_new")

        # Should get updated value now
        retrieved = get_value_cached(id=1)
        self.assertEqual(retrieved, "updated_1_new")

    def test_cache_put_with_kwargs_only(self):
        """Test CachePut with keyword arguments only"""

        @cache_put(namespace="kwarg_test", key="#item_id-#category")
        def process_item(item_id, category="default", extra=None):
            return {
                "processed_id": item_id,
                "category": category,
                "extra": extra
            }

        @cacheable(namespace="kwarg_test", key="#key", return_type=dict)
        def get_processed_item(key):
            return {}

        # Process with different kwargs
        result1 = process_item(item_id=100, category="electronics", extra="special")
        key1 = "100-electronics"

        result2 = process_item(item_id=100, category="books")
        key2 = "100-books"

        # Both should be cached separately
        cached1 = get_processed_item(key=key1)
        cached2 = get_processed_item(key=key2)

        self.assertEqual(cached1["category"], "electronics")
        self.assertEqual(cached2["category"], "books")

    def test_cache_put_returns_original_result(self):
        """Test that CachePut returns the original function result, not the cached value"""
        return_values = []

        @cache_put(namespace="return_test", key="#param")
        def test_function(param):
            result = f"result_{param}"
            return_values.append(result)
            return result

        @cacheable(namespace="return_test", key="#key", return_type=str)
        def get_cached(key):
            return None

        # First call
        result1 = test_function(param="test")
        self.assertEqual(result1, "result_test")
        self.assertEqual(return_values, ["result_test"])

        # Second call - should execute again (not cached)
        result2 = test_function(param="test")
        self.assertEqual(result2, "result_test")  # Same result
        self.assertEqual(return_values, ["result_test", "result_test"])  # Executed twice

        # But cache should have the value
        cached = get_cached(key="test")
        self.assertEqual(cached, "result_test")

    def test_cache_put_with_error_handling(self):
        """Test that CachePut doesn't cache when function raises an exception"""

        @cache_put(namespace="error_test", key="#param")
        def risky_function(param):
            if param == "fail":
                raise ValueError("Intentional failure")
            return f"success_{param}"

        @cacheable(namespace="error_test", key="#key", return_type=str)
        def get_from_cache(key):
            return None

        # Successful execution - should cache
        result1 = risky_function(param="success")
        self.assertEqual(result1, "success_success")

        cached1 = get_from_cache(key="success")
        self.assertEqual(cached1, "success_success")

        # Failed execution - should not cache
        with self.assertRaises(ValueError):
            risky_function(param="fail")

        # Nothing should be cached for "fail"
        cached_fail = get_from_cache(key="fail")
        self.assertIsNone(cached_fail)


class TestCacheEvictDecorator(unittest.TestCase):
    """Test CacheEvict decorator functionality"""

    def setUp(self):
        """Set up test environment"""
        Cache.initialize(
            os.environ.get("BROKER_TOKEN"),
            100)
        self.controller = Cache.get_instance()

    def tearDown(self):
        """Clean up after each test"""
        self.controller.evict_all()

    def test_cache_evict_specific_key(self):
        """Test CacheEvict removes specific cache entry"""
        call_count = {"get": 0}

        # Cacheable function
        @cacheable(namespace="users", key="#user_id", return_type=Person)
        def get_user_cached(user_id):
            call_count["get"] += 1
            return Person(first_name=f"User{user_id}", last_name="Doe")

        # CacheEvict function
        @cache_evict(namespace="users", key="#user_id")
        def delete_user(user_id):
            return f"Deleted user {user_id}"

        # First call - should execute
        result1 = get_user_cached(user_id=123)
        self.assertEqual(call_count["get"], 1)
        self.assertEqual(result1.first_name, "User123")

        # Second call - should use cache
        result2 = get_user_cached(user_id=123)
        self.assertEqual(call_count["get"], 1)

        # Evict the cache
        delete_result = delete_user(user_id=123)
        self.assertEqual(delete_result, "Deleted user 123")

        # Call again - should execute because cache was evicted
        result3 = get_user_cached(user_id=123)
        self.assertEqual(call_count["get"], 2)  # Counter increased!
        self.assertEqual(result3.first_name, "User123")

    def test_cache_evict_all_entries(self):
        """Test CacheEvict with all_entries=True removes entire namespace"""
        call_count = {"get": 0}

        @cacheable(namespace="products", key="#product_id", return_type=str)
        def get_product_cached(product_id):
            call_count["get"] += 1
            return f"Product{product_id}"

        @cache_evict(namespace="products", all_entries=True)
        def clear_product_cache():
            return "Cache cleared"

        # Populate cache with multiple entries
        result1 = get_product_cached(product_id=1)
        result2 = get_product_cached(product_id=2)
        result3 = get_product_cached(product_id=3)

        self.assertEqual(call_count["get"], 3)

        # All should be cached now
        result4 = get_product_cached(product_id=1)
        result5 = get_product_cached(product_id=2)
        result6 = get_product_cached(product_id=3)
        self.assertEqual(call_count["get"], 3)  # No increase

        # Clear entire namespace
        clear_result = clear_product_cache()
        self.assertEqual(clear_result, "Cache cleared")

        # All calls should now execute again
        result7 = get_product_cached(product_id=1)
        result8 = get_product_cached(product_id=2)
        result9 = get_product_cached(product_id=3)
        self.assertEqual(call_count["get"], 6)  # Increased by 3!

    def test_cache_evict_with_object_param(self):
        """Test CacheEvict with object parameter"""
        call_count = {"get": 0}

        @cacheable(namespace="user_details", key="#user.id")
        def get_user_details_cached(user):
            call_count["get"] += 1
            return f"Details for {user.first_name}"

        @cache_evict(namespace="user_details", key="#user.id")
        def update_user(user, new_name):
            user.first_name = new_name
            return f"Updated to {new_name}"

        user = Person(first_name="John", last_name="Doe", id=1)

        # Cache user details
        details1 = get_user_details_cached(user=user)
        self.assertEqual(call_count["get"], 1)

        # Should be cached
        details2 = get_user_details_cached(user=user)
        self.assertEqual(call_count["get"], 1)

        # Update user (evicts cache)
        update_result = update_user(user=user, new_name="Jonathan")
        self.assertEqual(update_result, "Updated to Jonathan")

        # Should execute again
        details3 = get_user_details_cached(user=user)
        self.assertEqual(call_count["get"], 2)
        self.assertEqual(details3, "Details for Jonathan")

    def test_cache_evict_with_result_in_key(self):
        """Test CacheEvict using result in key expression"""

        @cacheable(namespace="orders", key="#order_id", return_type=dict)
        def get_order_cached(order_id):
            return {"id": order_id, "status": "pending"}

        @cache_evict(namespace="orders", key="#result.id")
        def cancel_order(order_id):
            return {"id": order_id, "status": "cancelled"}

        # Cache an order
        order = get_order_cached(order_id=100)
        self.assertEqual(order["status"], "pending")

        # Cancel order - should evict cache entry with key 100
        cancelled = cancel_order(order_id=100)
        self.assertEqual(cancelled["status"], "cancelled")

        # Should execute again (not from cache)
        order_after = get_order_cached(order_id=100)
        self.assertEqual(order_after["status"], "pending")

    def test_cache_evict_specific_vs_all(self):
        """Test that specific key eviction doesn't affect other entries"""
        call_count = {"get": 0}

        @cacheable(namespace="mixed", key="#id", return_type=str)
        def get_item_cached(id):
            call_count["get"] += 1
            return f"Item{id}"

        @cache_evict(namespace="mixed", key="#id")
        def delete_specific(id):
            return f"Deleted {id}"

        # Cache multiple items
        item1 = get_item_cached(id=1)
        item2 = get_item_cached(id=2)
        item3 = get_item_cached(id=3)
        self.assertEqual(call_count["get"], 3)

        # All should be cached
        item1a = get_item_cached(id=1)
        item2a = get_item_cached(id=2)
        item3a = get_item_cached(id=3)
        self.assertEqual(call_count["get"], 3)

        # Evict only item 2
        delete_specific(id=2)

        # Item 1 and 3 should still be cached
        item1b = get_item_cached(id=1)
        item2b = get_item_cached(id=2)  # Should execute
        item3b = get_item_cached(id=3)

        self.assertEqual(call_count["get"], 4)  # Only increased by 1
        self.assertEqual(item2b, "Item2")  # Still works, just executed again

    def test_cache_evict_with_complex_key(self):
        """Test CacheEvict with complex key expressions"""

        @cacheable(namespace="transactions", key="#user_id-#tx_type", return_type=dict)
        def get_transaction_cached(user_id, tx_type):
            return {"user_id": user_id, "type": tx_type, "amount": 100}

        @cache_evict(namespace="transactions", key="#user_id-#tx_type")
        def process_transaction(user_id, tx_type):
            return {"processed": True, "user_id": user_id, "type": tx_type}

        # Cache a transaction
        tx1 = get_transaction_cached(user_id=123, tx_type="deposit")

        # Process it (evicts cache)
        process_result = process_transaction(user_id=123, tx_type="deposit")

        # Should execute again
        tx2 = get_transaction_cached(user_id=123, tx_type="deposit")

        # Different transaction type should not be affected
        tx3 = get_transaction_cached(user_id=123, tx_type="withdrawal")  # Should be cached if called before

    def test_cache_evict_returns_original_result(self):
        """Test that CacheEvict returns the function result, not the eviction result"""

        @cacheable(namespace="test", key="#id", return_type=str)
        def get_value(id):
            return f"value_{id}"

        @cache_evict(namespace="test", key="#id")
        def update_value(id, new_value):
            return f"updated_{new_value}"  # This is what should be returned

        # Cache a value
        get_value(id=1)

        # Update should return the function result
        result = update_value(id=1, new_value="test")
        self.assertEqual(result, "updated_test")  # Function result, not cache operation result

    def test_cache_evict_with_kwargs(self):
        """Test CacheEvict with keyword arguments"""

        @cacheable(namespace="config", key="#key-#subkey", return_type=dict)
        def get_config_cached(key, subkey="default"):
            return {"key": key, "subkey": subkey, "value": "config_value"}

        @cache_evict(namespace="config", key="#key-#subkey")
        def update_config(key, subkey="default", new_value=None):
            return {"key": key, "subkey": subkey, "value": new_value or "updated"}

        # Cache with different subkeys
        config1 = get_config_cached(key="app", subkey="database")
        config2 = get_config_cached(key="app", subkey="cache")

        # Evict only database config
        update_config(key="app", subkey="database", new_value="new_db_config")

        # Database config should execute again, cache config should still be cached
        config1_after = get_config_cached(key="app", subkey="database")
        config2_after = get_config_cached(key="app", subkey="cache")

    def test_cache_evict_with_error_handling(self):
        """Test that CacheEvict still returns result even if function raises exception"""

        @cacheable(namespace="error_test", key="#id", return_type=str)
        def get_with_error(id):
            return f"success_{id}"

        call_count = {"evict": 0}

        @cache_evict(namespace="error_test", key="#id")
        def risky_evict(id):
            call_count["evict"] += 1
            if id == "fail":
                raise ValueError("Intentional failure")
            return f"evicted_{id}"

        # Cache a value
        get_with_error(id="test")

        # Successful eviction
        result1 = risky_evict(id="test")
        self.assertEqual(result1, "evicted_test")
        self.assertEqual(call_count["evict"], 1)

        # Failed eviction - should still raise exception
        with self.assertRaises(ValueError):
            risky_evict(id="fail")

        self.assertEqual(call_count["evict"], 2)  # Still called

    def test_cache_evict_without_key_when_all_entries_false(self):
        """Test CacheEvict behavior when all_entries=False but no key provided"""

        # This should probably raise an error or have specific behavior
        # The test documents the expected behavior

        @cache_evict(namespace="test_ns")  # No key, all_entries defaults to False
        def some_operation():
            return "operation completed"

        with self.assertRaises(SyntaxError):
            some_operation()

    def test_cache_evict_multiple_namespaces(self):
        """Test CacheEvict on multiple namespaces with different strategies"""

        @cacheable(namespace="ns1", key="#id", return_type=str)
        def get_ns1(id):
            return f"ns1_{id}"

        @cacheable(namespace="ns2", key="#id", return_type=str)
        def get_ns2(id):
            return f"ns2_{id}"

        @cache_evict(namespace="ns1", key="#id")
        @cache_evict(namespace="ns2", all_entries=True)
        def complex_operation(id):
            return f"complex_{id}"

        # Populate both namespaces
        get_ns1(id=1)
        get_ns1(id=2)
        get_ns2(id=1)
        get_ns2(id=2)

        # Complex operation evicts specific key from ns1, all from ns2
        result = complex_operation(id=1)
        self.assertEqual(result, "complex_1")

        # ns1: id=1 should execute again, id=2 should be cached
        # ns2: both should execute again

    def test_cache_evict_before_return(self):
        """Verify cache is evicted before returning from function"""
        execution_order = []

        @cacheable(namespace="order_test", key="#id", return_type=str)
        def get_value(id):
            execution_order.append(f"get_{id}")
            return f"value_{id}"

        @cache_evict(namespace="order_test", key="#id")
        def evict_and_log(id):
            execution_order.append(f"before_evict_{id}")
            result = f"evicted_{id}"
            execution_order.append(f"after_evict_{id}")
            return result

        # Cache a value
        get_value(id=1)

        # Evict and check order
        eviction_result = evict_and_log(id=1)

        # Function should complete, then cache eviction happens in wrapper
        self.assertEqual(eviction_result, "evicted_1")

        # Call again to verify eviction happened
        get_value(id=1)

        # Execution order should show get, evict, get again
        self.assertIn("get_1", execution_order)
        # Should appear twice if eviction worked
        self.assertEqual(len([x for x in execution_order if x == "get_1"]), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
