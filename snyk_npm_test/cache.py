import json

import memcache

from .identifiers import PackageIdentifier


class Cache:
    def __init__(self, servers):
        self.mc = memcache.Client(servers)

    def get_dependencies(self, package_identifier: PackageIdentifier):
        deps = self.mc.get(package_identifier.cache_key)
        if deps:
            return json.loads(deps)

    def put_dependencies(self, package_identifier: PackageIdentifier, dependencies):
        self.mc.set(package_identifier.cache_key, json.dumps(dependencies))

    def get_versions(self, package_name):
        versions = self.mc.get(package_name)
        if versions:
            return json.loads(versions)

    def put_versions(self, package_name, versions):
        self.mc.set(package_name, json.dumps(versions), time=3600)
