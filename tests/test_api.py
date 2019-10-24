import pytest

from snyk_npm_test.api import app
from tests.test_cache import resolver_with_cache_entries


@pytest.mark.asyncio
async def test_tree(mocker, resolver_with_cache_entries):
    mocker.patch(
        "snyk_npm_test.api.get_resolver",
        lambda: resolver_with_cache_entries,
    )
    client = app.test_client()
    response = await client.get("/socket.io@2.3.0/tree")
    assert response.status_code == 200
    result = await response.get_json()
    assert list(result.keys()) == ["socket.io@2.3.0"]
    assert len(result["socket.io@2.3.0"]) == 6


@pytest.mark.asyncio
async def test_no_deps(mocker, resolver_with_cache_entries):
    mocker.patch(
        "snyk_npm_test.api.get_resolver",
        lambda: resolver_with_cache_entries,
    )
    client = app.test_client()
    package_identifier = "this-is-a-fake-package!!!-ssl@1.5.5"
    response = await client.get(f"/{package_identifier}/tree")
    assert response.status_code == 200
    result = await response.get_json()
    assert list(result.keys()) == [package_identifier]
    assert len(result[package_identifier]) == 0
