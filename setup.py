from glob import glob
from os.path import basename
from os.path import splitext

from setuptools import setup
from setuptools import find_packages


def _requires_from_file(filename):
    return open(filename).read().splitlines()


setup(
    name="airtable_client",
    version="0.1.0",
    description="A client library for Airtable.",
    author="Shikumiya, Inc.",
    url="https://github.com/shikumiya/airtable_client.git",
    packages="airtabler",
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
)