import asyncio
import unittest

from snyk_npm_test.npm import (
    PackageIdentifier,
    Semver,
    AmbiguousVersionStringError,
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


class TestVersionResolution(unittest.TestCase):
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
