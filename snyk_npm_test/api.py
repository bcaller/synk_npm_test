from quart import jsonify, Quart

from snyk_npm_test.npm import PackageIdentifier, NpmResolver, to_json_tree
from snyk_npm_test.cache import Cache


app = Quart(__name__)


@app.route('/<package>@<version>/flat')
async def packages(package, version):
    results = await NpmResolver(
        Cache(['127.0.0.1:11211']),
    ).recursively_get_dependencies(PackageIdentifier(package, version))
    return jsonify({
        str(package_identifier.cache_key): [
            str(dependency) for dependency in dependencies
        ]
        for package_identifier, dependencies in results.items()
    })


@app.route('/<package>@<version>/tree')
async def package_tree(package, version):
    root = PackageIdentifier(package, version)
    results = await NpmResolver(
        Cache(['127.0.0.1:11211']),
    ).recursively_get_dependencies(root)
    tree = to_json_tree(root, results)
    return jsonify({str(root): tree})


if __name__ == '__main__':
    app.run()
