import asyncio
import json

import pytest

from snyk_npm_test.npm import PackageIdentifier, NpmResolver
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


@pytest.fixture
def resolver():
    return NpmResolver(DictCache())


@pytest.fixture
def resolver_with_cache_entries():
    r = NpmResolver(DictCache())
    with open("tests/example-cache.json") as c:
        r.cache.mc._dict = json.loads(c.read())
    return r


@pytest.mark.asyncio
async def test_cached_versions(resolver):
    resolver.cache.mc.set("abc", '[["1.2.3", "4.5.6", "4.5.7"],{"next":"4.5.7"}]')
    identifier = await resolver.resolve_to_specific_version("abc", "^1.0.0")
    assert identifier == PackageIdentifier("abc", "1.2.3")
    identifier = await resolver.resolve_to_specific_version("abc", "next")
    assert identifier == PackageIdentifier("abc", "4.5.7")


@pytest.mark.asyncio
async def test_full_resolution_using_cache(resolver_with_cache_entries):
    dependencies = await resolver_with_cache_entries.recursively_get_dependencies(
        PackageIdentifier("socket.io", "2.3.0")
    )
    assert PackageIdentifier("this-is-a-fake-package!!!-ssl", "1.5.5") in dependencies
