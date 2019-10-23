import re

from typing import Dict, List, NamedTuple, Tuple

import requests


SPECIFIC_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


class PackageIdentifier(NamedTuple):
    package_name: str
    version_string: str


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


def resolve_to_specific_version(package_name: str, fuzzy_version_string: str) -> PackageIdentifier:
    if SPECIFIC_RE.fullmatch(fuzzy_version_string):  # Simple 12.34.56
        return PackageIdentifier(package_name, fuzzy_version_string)
    else:
        versions, dist_tags = get_package_versions(package_name)
        return PackageIdentifier(
            package_name,
            resolve_from_version_list(package_name, fuzzy_version_string, versions, dist_tags),
        )


def resolve_from_version_list(
    fuzzy_version_string: str, versions: List[str], dist_tags: Dict[str, str],
) -> str:
    print(versions, dist_tags)
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


def get_dependencies(package_identifier: PackageIdentifier):
    registry_response = requests.get(
        f"https://registry.npmjs.org/{package_identifier.package_name}/{package_identifier.version_string}",
    )
    registry_response.raise_for_status()
    dependencies_dict = registry_response.json()["dependencies"]
    return [
        resolve_to_specific_version(name, version_string)
        for name, version_string in dependencies_dict.items()
    ]


def get_package_versions(package_name: str) -> Tuple[List[str], Dict[str, str]]:
    registry_response = requests.get(
        f"https://registry.npmjs.org/{package_name}",
    ).json()
    versions_dict = registry_response["versions"]
    return list(versions_dict.keys()), registry_response["dist-tags"]
