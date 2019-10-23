import asyncio
import unittest

from app.npm import (
    PackageIdentifier,
    Semver,
    AmbiguousVersionStringError,
    NpmResolver,
)


class TestSemver(unittest.TestCase):
    def test_semver(self):
        assert Semver.from_string("0.12354.99") == (0, 12354, 99)
        assert str(Semver(0, 12354, 99)) == "0.12354.99"


class TestVersionResolution(unittest.TestCase):
    def setUp(self):
        self.resolver = NpmResolver()

    def test_specific_version(self):
        assert asyncio.run(self.resolver.resolve_to_specific_version("!", "0.2.3")) == PackageIdentifier(
            "!", "0.2.3",
        )

    def test_specific_version_with_tag(self):
        assert self.resolver.resolve_from_version_list("1.2.3-dev3", ["1.2.3-dev3"], {}) == "1.2.3-dev3"

    def test_tilde(self):
        assert self.resolver.resolve_from_version_list(
            "~0.0.1", ["0.1.2", "0.6.3", "0.0.1", "0.0.5", "1.9.9", "x"], {},
        ) == "0.0.5"
        assert self.resolver.resolve_from_version_list(
            "~1.0.1", ["0.1.2", "0.6.3", "0.0.1", "0.0.5", "1.0.3", "1.0.1", "1.1.1", "1.9.0", "x"], {},
        ) == "1.0.3"

    def test_caret(self):
        assert self.resolver.resolve_from_version_list(
            "^0.0.1", ["0.1.2", "0.6.3", "0.0.1", "0.0.5", "1.9.9", "x"], {},
        ) == "0.0.1", "^0.0.X should give exact version"
        assert self.resolver.resolve_from_version_list(
            "^0.1.1", ["0.1.2", "0.6.3", "0.0.1", "0.0.5", "1.9.9", "x"], {},
        ) == "0.1.2", "^0.X.Y should give 0.X.*"
        self.assertEqual(self.resolver.resolve_from_version_list(
            "^1.0.1", ["0.1.2", "0.6.3", "0.0.1", "0.0.5", "1.0.3", "1.0.1", "1.1.1", "1.9.0", "x"], {},
        ), "1.9.0", "^X.Y.Z should give X.*.*")
