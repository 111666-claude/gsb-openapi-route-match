import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routematch import core


def route(name, path, method="GET", host=""):
    return {"name": name, "path": path, "method": method, "host": host}


class RouteMatchTest(unittest.TestCase):
    def test_static_match(self):
        router = core.Router([route("x", "/a")])
        self.assertEqual(router.match("GET", "", "/a", core.Counter()), "x")

    def test_no_match(self):
        router = core.Router([route("x", "/a")])
        self.assertEqual(router.match("GET", "", "/b", core.Counter()), "")

    def test_param_match(self):
        router = core.Router([route("y", "/a/{id}")])
        self.assertEqual(router.match("GET", "", "/a/z", core.Counter()), "y")

    def test_empty_routes(self):
        self.assertEqual(core.Router([]).match("GET", "", "/a", core.Counter()), "")

    def test_method_match(self):
        router = core.Router([route("m", "/a", method="POST")])
        self.assertEqual(router.match("POST", "", "/a", core.Counter()), "m")

    def test_counter_counts(self):
        router = core.Router([route("x", "/a")])
        counter = core.Counter()
        router.match("GET", "", "/a", counter)
        self.assertGreater(counter.scanned, 0)


if __name__ == "__main__":
    unittest.main()
