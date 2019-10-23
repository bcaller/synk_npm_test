import asyncio
import re

from typing import Dict, List, NamedTuple, Tuple

import aiohttp
import requests


SPECIFIC_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


class PackageIdentifier(NamedTuple):
    package_name: str
    version_string: str

    def __repr__(self):
        return f"{self.package_name}@{self.version_string}"


class Semver(NamedTuple):
    major: int
    minor: int
    patch: int

    @classmethod
    def from_string(cls, version: str):
        return Semver(*tuple(int(x) for x in SPECIFIC_RE.fullmatch(version).groups()))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


class AmbiguousVersionStringError(Exception):
    def __init__(self, version_string: str, version_data):
        super().__init__(f"Cannot resolve version string '{version_string}' with {version_data}")
        self.version_string = version_string
        self.version_data = version_data


class NpmResolver:
    async def resolve_to_specific_version(
        self, package_name: str, fuzzy_version_string: str,
    ) -> PackageIdentifier:
        if SPECIFIC_RE.fullmatch(fuzzy_version_string):  # Simple 12.34.56
            return PackageIdentifier(package_name, fuzzy_version_string)
        else:
            versions, dist_tags = await self.get_package_versions(package_name)
            return PackageIdentifier(
                package_name,
                self.resolve_from_version_list(fuzzy_version_string, versions, dist_tags),
            )

    def resolve_from_version_list(
        self, fuzzy_version_string: str, versions: List[str], dist_tags: Dict[str, str],
    ) -> str:
        if fuzzy_version_string in dist_tags:  # e.g. next
            return dist_tags[fuzzy_version_string]
        if fuzzy_version_string in versions:  # e.g. 2.1.3rc7x
            return fuzzy_version_string
        semver = (
            Semver.from_string(version)
            for version in versions
            if SPECIFIC_RE.fullmatch(version)
        )
        if fuzzy_version_string[0] in ('~', '^') and SPECIFIC_RE.fullmatch(fuzzy_version_string[1:]):
            # ^12.34.56, ^12.0.0, ^0.1.0, ^0.0.3 or ~12.34.56
            base_version = Semver.from_string(fuzzy_version_string[1:])
            if fuzzy_version_string[0] == '~' or (base_version.major == 0 and base_version.minor > 0):
                acceptable = (
                    s for s in semver
                    if s[:2] == base_version[:2] and s.patch >= base_version.patch
                )
            elif base_version.major == base_version.minor == 0:
                return str(base_version)
            else:
                acceptable = (
                    s for s in semver
                    if s.major == base_version.major and (
                        s.minor > base_version.minor or
                        (s.minor == base_version.minor and s.patch >= base_version.patch)
                    )
                )
            return str(max(acceptable))
        raise AmbiguousVersionStringError(fuzzy_version_string, (versions, dist_tags))

    async def recursively_get_dependencies(self, package_identifier: PackageIdentifier, results=None):
        results = {} if results is None else results
        assert package_identifier not in results
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
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://registry.npmjs.org/{package_identifier.package_name}/{package_identifier.version_string}"
            ) as registry_response:
                json_response = await registry_response.json()
                dependencies_dict = json_response.get("dependencies", {})
                tasks = [
                    self.resolve_to_specific_version(name, version_string)
                    for name, version_string in dependencies_dict.items()
                ]
                results = await asyncio.gather(*tasks)
                return results


    async def get_package_versions(self, package_name: str) -> Tuple[List[str], Dict[str, str]]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://registry.npmjs.org/{package_name}"
            ) as registry_response:
                json_response = await registry_response.json()
                versions_dict = json_response["versions"]
                return list(versions_dict.keys()), json_response["dist-tags"]
