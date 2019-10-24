import asyncio
import re

from typing import Dict, List, NamedTuple, Tuple

import aiohttp

from snyk_npm_test.identifiers import PackageIdentifier, Semver


class AmbiguousVersionStringError(Exception):
    def __init__(self, version_string: str, version_data):
        super().__init__(
            f"Cannot resolve version string '{version_string}' with {version_data}"
        )
        self.version_string = version_string
        self.version_data = version_data


class NpmResolver:
    def __init__(self, cache=None):
        self.cache = cache

    async def resolve_to_specific_version(
        self, package_name: str, fuzzy_version_string: str
    ) -> PackageIdentifier:
        if Semver.is_semver(fuzzy_version_string):  # Simple 12.34.56
            return PackageIdentifier(package_name, fuzzy_version_string)
        else:
            versions, dist_tags = await self.get_package_versions(package_name)
            return PackageIdentifier(
                package_name,
                self.resolve_from_version_list(
                    fuzzy_version_string, versions, dist_tags
                ),
            )

    def resolve_from_version_list(
        self, fuzzy_version_string: str, versions: List[str], dist_tags: Dict[str, str]
    ) -> str:
        """This is gross and non-exhaustive."""
        if (tagged_version := dist_tags.get(fuzzy_version_string)):  # e.g. next
            return tagged_version
        if fuzzy_version_string in versions:  # e.g. 2.1.3rc7x
            return fuzzy_version_string
        semver = (
            Semver.from_string(version)
            for version in versions
            if Semver.is_semver(version)
        )
        if fuzzy_version_string[0] in ("~", "^") and Semver.is_semver(
            fuzzy_version_string[1:]
        ):
            # ^12.34.56, ^12.0.0, ^0.1.0, ^0.0.3 or ~12.34.56
            base_version = Semver.from_string(fuzzy_version_string[1:])
            if fuzzy_version_string[0] == "~" or (
                base_version.major == 0 and base_version.minor > 0
            ):
                acceptable = (
                    s
                    for s in semver
                    if s[:2] == base_version[:2] and s.patch >= base_version.patch
                )
            elif base_version.major == base_version.minor == 0:
                return str(base_version)
            else:
                acceptable = (
                    s
                    for s in semver
                    if s.major == base_version.major
                    and (
                        s.minor > base_version.minor
                        or (
                            s.minor == base_version.minor
                            and s.patch >= base_version.patch
                        )
                    )
                )
            return str(max(acceptable))

        if (conditions := re.findall(r"([><]=?)\s*(\d+(?:\.\d+){0,2})", fuzzy_version_string)):
            semver = list(semver)
            for (comparator, version) in conditions:
                fixed_version = Semver.from_partial_string(version)
                if comparator == ">":
                    predicate = lambda x: x > fixed_version
                elif comparator == ">=":
                    predicate = lambda x: x >= fixed_version
                elif comparator == "<":
                    predicate = lambda x: x < fixed_version
                else:
                    predicate = lambda x: x <= fixed_version
                semver = [s for s in semver if predicate(s)]
            return str(max(semver))
        raise AmbiguousVersionStringError(fuzzy_version_string, (versions, dist_tags))

    async def recursively_get_dependencies(
        self, package_identifier: PackageIdentifier, results=None
    ):
        results = {} if results is None else results
        if package_identifier in results:
            return results
        results[package_identifier] = []
        dependencies = await self.get_dependencies(package_identifier)
        tasks = []
        for dependency in dependencies:
            results[package_identifier].append(dependency)
            if dependency not in results:
                tasks.append(self.recursively_get_dependencies(dependency, results))
        await asyncio.gather(*tasks)
        return results

    async def get_dependencies(self, package_identifier: PackageIdentifier):
        if self.cache:
            cached = self.cache.get_dependencies(package_identifier)
            if cached is not None:  # Can be empty list
                return [PackageIdentifier(*d) for d in cached]
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://registry.npmjs.org/{package_identifier.package_name}/{package_identifier.version_string}"
            ) as registry_response:
                registry_response.raise_for_status()
                json_response = await registry_response.json()
                dependencies_dict = json_response.get("dependencies", {})
                tasks = [
                    self.resolve_to_specific_version(name, version_string)
                    for name, version_string in dependencies_dict.items()
                ]
                results = await asyncio.gather(*tasks)
                if self.cache:
                    self.cache.put_dependencies(package_identifier, results)
                return results

    async def get_package_versions(
        self, package_name: str
    ) -> Tuple[List[str], Dict[str, str]]:
        if self.cache:
             if (cached := self.cache.get_versions(package_name)):
                return PackageIdentifier(cached[0], cached[1])
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://registry.npmjs.org/{package_name}"
            ) as registry_response:
                json_response = await registry_response.json()
                versions_dict = json_response["versions"]
                results = list(versions_dict.keys()), json_response["dist-tags"]
                if self.cache:
                    self.cache.put_versions(package_name, [results[0], results[1]])
                return results


def to_json_tree(root, package_to_dependencies_mapping):
    return {
        str(package): to_json_tree(package, package_to_dependencies_mapping)
        for package in package_to_dependencies_mapping[root]
    }
