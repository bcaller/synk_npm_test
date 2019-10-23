from setuptools import setup

setup(
    name="snyk_npm_test",
    packages=["app"],
    test_suite='tests',
    install_requires=["aiohttp", "quart"],
)
