from quart import Quart

from npm import PackageIdentifier, NpmResolver


app = Quart(__name__)

@app.route('/<package>@<version>')
async def packages(package, version):
    assert '@' not in package
    results = await NpmResolver().recursively_get_dependencies(PackageIdentifier(package, version))
    return repr(results)

app.run()
