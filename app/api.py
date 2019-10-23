from quart import Quart

from npm import PackageIdentifier, recursively_get_dependencies


app = Quart(__name__)

@app.route('/<package>@<version>')
async def packages(package, version):
    assert '@' not in package
    results = await recursively_get_dependencies(PackageIdentifier(package, version))
    return repr(results)

app.run()
