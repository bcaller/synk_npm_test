import asyncio

import pytest
from hypothesis import given, strategies as st

from snyk_npm_test.npm import (
    PackageIdentifier,
    Semver,
    AmbiguousVersionStringError,
    NpmResolver,
)


@given(major=st.integers(0), minor=st.integers(0), patch=st.integers(0))
def test_semver(major, minor, patch):
    string = f"{major}.{minor}.{patch}"
    semver = Semver.from_string(string)
    assert semver == (major, minor, patch)
    assert str(semver) == string

@given(st.integers(0).map(str))
def test_semver_partial_major(s):
    assert Semver.from_partial_string(s) == (int(s), 0, 0)

@given(st.integers(0), st.integers(0))
def test_semver_partial_major_minor(major, minor):
    s = f"{major}.{minor}"
    assert Semver.from_partial_string(s) == (major, minor, 0)


def test_semver_partial():
    assert Semver.from_partial_string("0.12354.99") == (0, 12354, 99)
    assert Semver.from_partial_string("0.12354") == (0, 12354, 0)
    assert Semver.from_partial_string("9") == (9, 0, 0)


@pytest.fixture
def resolver():
    return NpmResolver()


@pytest.mark.asyncio
async def test_specific_version(resolver):
    identifier = await resolver.resolve_to_specific_version("!", "0.2.3")
    assert identifier == PackageIdentifier("!", "0.2.3")


def test_specific_version_with_tag(resolver):
    assert (
        resolver.resolve_from_version_list("1.2.3-dev3", ["1.2.3-dev3"], {})
        == "1.2.3-dev3"
    )


def test_tilde(resolver):
    assert (
        resolver.resolve_from_version_list(
            "~0.0.1", ["0.1.2", "0.6.3", "0.0.1", "0.0.5", "1.9.9", "x"], {}
        )
        == "0.0.5"
    )
    assert (
        resolver.resolve_from_version_list(
            "~1.0.1",
            [
                "0.1.2",
                "0.6.3",
                "0.0.1",
                "0.0.5",
                "1.0.3",
                "1.0.1",
                "1.1.1",
                "1.9.0",
                "x",
            ],
            {},
        )
        == "1.0.3"
    )


def test_caret(resolver):
    assert (
        resolver.resolve_from_version_list(
            "^0.0.1", ["0.1.2", "0.6.3", "0.0.1", "0.0.5", "1.9.9", "x"], {}
        )
        == "0.0.1"
    ), "^0.0.X should give exact version"
    assert (
        resolver.resolve_from_version_list(
            "^0.1.1", ["0.1.2", "0.6.3", "0.0.1", "0.0.5", "1.9.9", "x"], {}
        )
        == "0.1.2"
    ), "^0.X.Y should give 0.X.*"
    assert (
        resolver.resolve_from_version_list(
            "^1.0.1",
            [
                "0.1.2",
                "0.6.3",
                "0.0.1",
                "0.0.5",
                "1.0.3",
                "1.0.1",
                "1.1.1",
                "1.9.0",
                "x",
            ],
            {},
        )
        == "1.9.0"
    ), "^X.Y.Z should give X.*.*"


def test_conditions(resolver):
    assert (
        resolver.resolve_from_version_list(">2 <3", ["1.0.1", "2.9.9", "4.5.6"], {})
        == "2.9.9"
    )
    assert (
        resolver.resolve_from_version_list(">2 >=3", ["1.0.1", "2.9.9", "4.5.6"], {})
        == "4.5.6"
    )
    assert (
        resolver.resolve_from_version_list("<=2.3", ["1.0.1", "2.9.9"], {}) == "1.0.1"
    )
    assert (
        resolver.resolve_from_version_list("<=2.3", ["1.0.1", "2.2.2", "5.5.5"], {})
        == "2.2.2"
    )
