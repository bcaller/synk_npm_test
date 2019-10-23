import re
from typing import NamedTuple


SPECIFIC_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


class PackageIdentifier(NamedTuple):
    package_name: str
    version_string: str

    def __str__(self) -> str:
        return f"{self.package_name}@{self.version_string}"

    @property
    def cache_key(self) -> str:
        return str(self)

    def __repr__(self):
        return str(self)


class Semver(NamedTuple):
    major: int
    minor: int
    patch: int

    @classmethod
    def is_semver(cls, version: str):
        return bool(SPECIFIC_RE.fullmatch(version))

    @classmethod
    def from_string(cls, version: str):
        return Semver(*tuple(int(x) for x in SPECIFIC_RE.fullmatch(version).groups()))

    @classmethod
    def from_partial_string(cls, version: str):
        parts = [int(x) for x in version.split('.')]
        n = len(parts)
        if n == 0 or n > 3:
            raise ValueError("Impossible")
        elif n == 1:
            return Semver(parts[0], 0, 0)
        elif n == 2:
            return Semver(parts[0], parts[1], 0)
        else:
            return Semver(*parts)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

