from quart import jsonify, Quart

from snyk_npm_test.npm import PackageIdentifier, NpmResolver, to_json_tree
from snyk_npm_test.cache import Cache


app = Quart(__name__)


def get_resolver():
    return NpmResolver(Cache(['127.0.0.1:11211']))


@app.route('/<package>@<version>/flat')
async def packages(package, version):
    resolver = get_resolver()
    root = await resolver.resolve_to_specific_version(package, version)
    results = await resolver.recursively_get_dependencies(root)
    return jsonify({
        str(package_identifier): [
            str(dependency) for dependency in dependencies
        ]
        for package_identifier, dependencies in results.items()
    })


@app.route('/<package>@<version>/tree')
async def package_tree(package, version):
    resolver = get_resolver()
    root = await resolver.resolve_to_specific_version(package, version)
    results = await resolver.recursively_get_dependencies(root)
    tree = to_json_tree(root, results)
    return jsonify({str(root): tree})


if __name__ == '__main__':
    app.run()
