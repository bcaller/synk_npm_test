from setuptools import setup

setup(
    name="snyk_npm_test",
    packages=["snyk_npm_test"],
    test_suite='tests',
    install_requires=["aiohttp", "quart", "python-memcached"],
)
