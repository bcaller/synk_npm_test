import asyncio
import json
import unittest

from snyk_npm_test.npm import (
    PackageIdentifier,
    NpmResolver,
)
from snyk_npm_test.cache import Cache


class DictMemcache:
    def __init__(self):
        self._dict = {}

    def get(self, x):
        return self._dict.get(x)

    def set(self, k, v, time=None):
        self._dict[k] = v


class DictCache(Cache):
    def __init__(self):
        super().__init__([])
        self.mc = DictMemcache()


class TestNpmResolutionWithCache(unittest.TestCase):
    def setUp(self):
        self.resolver = NpmResolver(
            DictCache()
        )

    def test_cached_versions(self):
        self.resolver.cache.mc.set(
            "abc",
            '[["1.2.3", "4.5.6", "4.5.7"],{"next":"4.5.7"}]',
        )
        assert asyncio.run(
            self.resolver.resolve_to_specific_version("abc", "^1.0.0")
        ) == PackageIdentifier(
            "abc", "1.2.3",
        )

        assert asyncio.run(
            self.resolver.resolve_to_specific_version("abc", "next")
        ) == PackageIdentifier(
            "abc", "4.5.7",
        )

    def test_full_resolution_using_cache(self):
        with open("tests/example-cache.json") as c:
            self.resolver.cache.mc._dict = json.loads(c.read())
        dependencies = asyncio.run(
            self.resolver.recursively_get_dependencies(
                PackageIdentifier("socket.io", "2.3.0")
            )
        )
        assert PackageIdentifier("this-is-a-fake-package!!!-ssl", "1.5.5") in dependencies
