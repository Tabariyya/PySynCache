import unittest

from SynCache.Controller import Controller
from SynCache.decorators import _eval_expr, cacheable


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


class TestController(unittest.TestCase):

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
        Controller.initialize("ws://91.93.135.176:25672/",
                              "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjI2MjgwMjc2MDUsInN1YiI6Imdvb2dsZSJ9.XgGmtV7ffxFI_a_g6U7lT_6mn2hc7RvJhO3lukUgMhRflgA5UwwHPt-5c5-uF_wsyA3HPmwQg_cjvI_JrG122OHqbC7Y-16059W-r4W_QALEgHHZKcijf_5g1CsG4DjGfHYJI4JmwrogQ0_yj4UUCD6OMY5v5g0QH4FCsxWcaI4",
                              100)
        self.controller = Controller.get_instance()

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


if __name__ == '__main__':
    unittest.main(verbosity=2)
