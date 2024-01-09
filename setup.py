from setuptools import setup, find_packages

from fastapi_imp import __version__

setup(
    name="fastapi-imp",
    version=__version__,
    author="eatmoreapple",
    description="class base view for fastapi",
    url="https://github.com/eatmoreapple/fastapi_imp",
    packages=find_packages(),
    author_email="eatmoreorange@gmail.com",
    install_requires=[
        'fastapi',
    ]
)
